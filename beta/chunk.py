import StringIO

from nbt.nbt import TAG_Compound
from nbt.nbt import TAG_Int

from beta.alpha import Inventory
from beta.packets import make_packet
from beta.utilities import triplet_to_index, pack_nibbles, unpack_nibbles

class TileEntity(object):

    def load_from_tag(self, tag):
        self.x = tag["x"].value
        self.y = tag["y"].value
        self.z = tag["z"].value

    def save_to_tag(self):
        tag = TAG_Compound()
        tag["x"] = TAG_Int(self.x)
        tag["y"] = TAG_Int(self.y)
        tag["z"] = TAG_Int(self.z)

        return tag

    def save_to_packet(self):
        tag = self.save_to_tag()
        sio = StringIO.StringIO()
        tag._render_buffer(sio)

        packet = make_packet("tile", x=self.x, y=self.y, z=self.z,
            nbt=sio.getvalue())
        return packet

class Chest(TileEntity):

    def load_from_tag(self, tag):
        super(Chest, self).load_from_tag(tag)

        self.inventory = Inventory(0, 0, 36)
        self.inventory.load_from_tag(tag["Items"])

    def save_to_tag(self):
        tag = super(Chest, self).save_to_tag()

        items = self.inventory.save_to_tag()
        tag["Items"] = items

        return tag

tileentity_names = {
    "Chest": Chest,
}

class Chunk(object):

    def __init__(self, x, z):
        self.x = int(x)
        self.z = int(z)

        self.blocks = [0] * 16 * 128 * 16
        self.heightmap = [0] * 16 * 16
        self.lightmap = [0] * 16 * 128 * 16
        self.metadata = [0] * 16 * 128 * 16
        self.skylight = [0] * 16 * 128 * 16

        self.tileentities = []

    def regenerate_heightmap(self):
        pass

    def regenerate_lightmap(self):
        pass

    def regenerate_metadata(self):
        pass

    def regenerate_skylight(self):
        pass

    def regenerate(self):
        """
        Regenerate all extraneous tables.
        """

        self.regenerate_heightmap()
        self.regenerate_lightmap()
        self.regenerate_metadata()
        self.regenerate_skylight()

    def load_from_tag(self, tag):
        level = tag["Level"]
        self.blocks = [ord(i) for i in level["Blocks"].value]
        self.heightmap = [ord(i) for i in level["HeightMap"].value]
        self.lightmap = unpack_nibbles(level["BlockLight"].value)
        self.metadata = unpack_nibbles(level["Data"].value)
        self.skylight = unpack_nibbles(level["SkyLight"].value)

        if level["TileEntities"].value:
            for tag in level["TileEntities"].value:
                try:
                    te = tileentity_names[tag["id"].value]()
                    te.load_from_tag(tag)
                    self.tileentities.append(te)
                except:
                    print "Unknown tile entity %s" % tag["id"].value

    def save_to_packet(self):
        """
        Generate a chunk packet.
        """

        array = [chr(i) for i in self.blocks]
        array += pack_nibbles(self.metadata)
        array += pack_nibbles(self.lightmap)
        array += pack_nibbles(self.skylight)
        packet = make_packet("chunk", x=self.x * 16, y=0, z=self.z * 16,
            x_size=15, y_size=127, z_size=15, data="".join(array))
        return packet

    def get_block(self, coords):
        """
        Look up a block value.
        """

        index = triplet_to_index(coords)

        return self.blocks[index]

    def set_block(self, coords, block):
        """
        Update a block value.
        """

        index = triplet_to_index(coords)

        self.blocks[index] = block

    def height_at(self, x, z):
        """
        Get the height of an x-z column of blocks.
        """

        return self.heightmap[x * 16 + z]
