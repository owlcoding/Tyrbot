from core.decorators import instance, command
from core.command_param_types import Regex, Int, Any
from core.db import DB
from core.text import Text
from core.chat_blob import ChatBlob


@instance()
class PlayfieldController:
    def inject(self, registry):
        self.db: DB = registry.get_instance("db")
        self.text: Text = registry.get_instance("text")
        self.command_alias_service = registry.get_instance("command_alias_service")

    def start(self):
        self.command_alias_service.add_alias("playfields", "playfield")

    @command(command="playfield", params=[], access_level="all",
             description="Show a list of playfields")
    def playfield_list_command(self, request):
        data = self.db.query("SELECT * FROM playfields ORDER BY long_name")

        blob = ""
        for row in data:
            blob += "[<highlight>%d<end>] %s (%s)\n" % (row.id, row.long_name, row.short_name)

        return ChatBlob("Playfields", blob)

    @command(command="waypoint", params=[Regex("waypoint_data", "\s+.*?Pos: ([0-9.]+), ([0-9.]+), ([0-9.]+), Area: ([a-zA-Z ]+).*", num_groups=4)], access_level="all",
             description="Create a waypoint link from F9 output", extended_description="Example: <symbol>waypoint Pos: 123.1, 456.1, 789.1, Area: Perpetual Wastelands")
    def waypoint1_command(self, request, regex):
        x_coords, y_coords, _, playfield_arg = regex

        return self.create_waypoint_blob(x_coords, y_coords, playfield_arg)

    @command(command="waypoint", params=[Regex("waypoint_data", "\s+.*?([0-9.]+) ([0-9.]+) y ([0-9.]+) ([0-9]+).*", num_groups=4)], access_level="all",
             description="Create a waypoint link from Shift + F9 output", extended_description="Example: <symbol>waypoint 123.1 456.1 y 789.1 570")
    def waypoint2_command(self, request, regex):
        x_coords, y_coords, _, playfield_arg = regex

        return self.create_waypoint_blob(x_coords, y_coords, playfield_arg)

    @command(command="waypoint", params=[Int("x_coords"), Int("y_coords"), Any("playfield")], access_level="all",
             description="Manually create a waypoint link", extended_description="Example: !waypoint 123 456 PW")
    def waypoint3_command(self, request, x_coords, y_coords, playfield_arg):
        return self.create_waypoint_blob(x_coords, y_coords, playfield_arg)

    def create_waypoint_blob(self, x_coords, y_coords, playfield_arg):
        playfield = self.get_playfield_by_name(playfield_arg) or self.get_playfield_by_id(playfield_arg)

        if not playfield:
            return "Could not find playfield <highlight>%s<end>." % playfield_arg
        else:
            title = "waypoint: %sx%s %s" % (x_coords, y_coords, playfield.long_name)
            blob = "Click here to use waypoint: "
            blob += self.text.make_chatcmd(title, "/waypoint %s %s %d" % (x_coords, y_coords, playfield.id))
            return ChatBlob(title, blob)

    def get_playfield_by_name(self, name):
        return self.db.query_single("SELECT * FROM playfields WHERE long_name LIKE ? OR short_name LIKE ? LIMIT 1", [name, name])

    def get_playfield_by_id(self, playfield_id):
        return self.db.query_single("SELECT * FROM playfields WHERE id = ?", [playfield_id])
