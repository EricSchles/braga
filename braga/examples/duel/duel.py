from collections import defaultdict

from braga import Assemblage, Component, System, Aspect


#################################################
# Define components for players, rooms, and wand
#################################################
class Name(Component):
    """A name for the Entity. For players and wands."""

    INITIAL_PROPERTIES = ['name']

    def __init__(self, name=None):
        self.name = name


class Description(Component):
    """A description of the Entity. For all entities."""

    INITIAL_PROPERTIES = ['description']

    def __init__(self, description=None):
        self.description = description


class Container(Component):
    """Ability to have an inventory. For rooms and players."""
    pass


class EquipmentBearing(Component):
    """Can use Equipment. For players."""
    pass


class Mappable(Component):
    """ Ability to be part of a map, stores links to other objects on map.
        For rooms only.
    """

    def __init__(self, paths=None):
        self.paths = paths if paths else dict()


class Moveable(Component):
    """Ability to be moved, stores Entity's location. For players and wands."""

    INITIAL_PROPERTIES = ['location']

    def __init__(self, location=None):
        self.location = location


class Equipment(Component):
    """Ability to be equipped. Stores what type of equipment the Entity is. For wands."""

    INITIAL_PROPERTIES = ['equipment_type', 'bearer']

    def __init__(self, equipment_type, bearer=None):
        self.equipment_type = equipment_type
        self.bearer = bearer


class Loyalty(Component):
    """Tracks what other Entity this Entity is loyal / belongs to. For wands."""

    INITIAL_PROPERTIES = ['owner']

    def __init__(self, owner=None):
        self.owner = owner


class ExpelliarmusSkill(Component):
    """Ability to cast expelliarmus, stores skill at casting expelliarmus. For players."""

    def __init__(self):
        self.skill = 0


#####################################
# Define systems to manage components
#####################################
class ContainerSystem(System):
    """Manages Containers and the Moveables they contain."""
    def __init__(self, world, auto_update=False):
        super(ContainerSystem, self).__init__(world=world, aspect=Aspect(all_of=set([Container])))
        self.inventories = defaultdict(set)
        self.auto_update = auto_update
        for entity in self.world.entities_with_aspect(Aspect(all_of=set([Moveable]))):
            self.inventories[entity.location].add(entity)
        self.update()

    def update(self):
        """Updates the `inventory` attribute on all Containers in the World"""
        for entity in self.world.entities_with_aspect(Aspect(all_of=set([Moveable]))):
            self.inventories[entity.location].add(entity)
        for entity in self.entities:
            setattr(entity, 'inventory', self.inventories[entity])

    def move(self, thing, new_container, auto_update=False):
        """Moves a Moveable into a Container."""
        if not thing.has_component(Moveable):
            raise ValueError("You cannot move this item")
        if not new_container in self.aspect:
            raise ValueError("Invalid destination")
        old_container = thing.location
        thing.location = new_container
        self.inventories[new_container].add(thing)
        if old_container:
            self.inventories[old_container].remove(thing)
        self.update()


class EquipmentSystem(System):
    """Manager for Equipment and its bearers."""
    def __init__(self, world, auto_update=False):
        super(EquipmentSystem, self).__init__(world=world, aspect=Aspect(all_of=set([EquipmentBearing])))
        self.equipment = defaultdict(lambda: None)
        self.auto_update = auto_update
        self.update()

    def equip(self, bearer, item, auto_update=False):
        """Equip an Entity with another Entity"""
        if not bearer in self:
            raise ValueError("That cannot equip other items")
        if not item in self.world.entities_with_aspect(Aspect(all_of=set([Equipment]))):
            raise ValueError("That item cannot be equipped")
        if self.equipment[bearer]:
            raise ValueError("You cannot equip that at this time")
        self.equipment[bearer] = item
        self.update()

    def unequip(self, bearer, item):
        """Unequip an Entity from the Entity equipping it."""
        del self.equipment[bearer]
        delattr(bearer, item.equipment_type)

    def update(self):
        for entity in self.entities:
            item = self.equipment[entity]
            if item:
                setattr(entity, item.equipment_type, item)
                item.bearer = entity


class NameSystem(System):
    """Associates strings with Entities."""
    def __init__(self, world):
        super(NameSystem, self).__init__(world=world, aspect=Aspect(all_of=set([Name])))
        self.names = defaultdict(lambda: None)
        self.update()

    @property
    def tokens(self):
        return self.names.keys()

    def get_entity_from_name(self, name):
        return self.names.get(name)

    def add_alias(self, alias, entity):
        if alias in self.names.keys():
            raise ValueError("Duplicate entity names")
        self.names[alias] = entity

    def update(self):
        for entity in self.entities:
            self.names[entity.name] = entity


#########################
# Define what a player is
#########################

player_factory = Assemblage(components=[Name, Description, Container, Moveable, EquipmentBearing, ExpelliarmusSkill])

########################
# Define what a room is
########################

room_factory = Assemblage(components=[Description, Container, Mappable, Name])

#######################
# Define what a wand is
#######################

wand_factory = Assemblage(components=[Name, Description, Equipment, Moveable, Loyalty], equipment_type='wand')
