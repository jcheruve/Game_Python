import actions
import point

BLOB_RATE_SCALE = 4

class Entity(object):
   def __init__(self, name, imgs):
      self.name = name
      self.imgs = imgs
      self.current_img = 0

   def get_name(self):
      return self.name
   def get_images(self):
      return self.imgs
   def get_image(self):
      return self.imgs[self.current_img]

class Background(Entity):
   def __init__(self, name, imgs):
   	   super(Background, self).__init__(name, imgs)

class On_Board(Entity):
   def __init__(self, name, imgs, position):
   	   super(On_Board, self).__init__(name, imgs)
	   self.position = position

   def set_position(self, point):
      self.position = point
   def get_position(self):
      return self.position
   def get_images(self):
      return self.imgs
   def get_image(self):
      return self.imgs[self.current_img]
   def get_name(self):
      return self.name
   def next_image(self):
      self.current_img = (self.current_img + 1) % len(self.imgs)

class Obstacle(On_Board):
   def __init__(self, name, position, imgs):
      super(Obstacle, self).__init__(name, imgs, position)

   def entity_string(self):
      return ' '.join(['obstacle', entity.name, str(entity.position.x),
         str(entity.position.y)])

class Action_Entity(On_Board):
   def __init__(self, name, position, imgs):
	   super(Action_Entity, self).__init__(name, imgs, position)
	   self.pending_actions = []

   def remove_pending_action(self, action):
      if hasattr(self, "pending_actions"):
         self.pending_actions.remove(action)
   def add_pending_action(self, action):
      if hasattr(self, "pending_actions"):
         self.pending_actions.append(action)
   def get_pending_actions(self):
      if hasattr(self, "pending_actions"):
         return self.pending_actions
      else:
         return []
   def clear_pending_actions(self):
      if hasattr(self, "pending_actions"):
         self.pending_actions = []
   def remove_entity(self, world):
      for action in self.get_pending_actions():
         world.unschedule_action(action)
      self.clear_pending_actions()
      world.remove_entity(self)

class Vein(Action_Entity):
   def __init__(self, name, rate, position, imgs, resource_distance=1):
      super(Vein, self).__init__(name, position, imgs)
      self.rate = rate
      self.resource_distance = resource_distance

   def get_rate(self):
      return self.rate
   def get_resource_distance(self):
      return self.resource_distance
   def entity_string(self):
      return ' '.join(['vein', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate),
         str(entity.resource_distance)])
   def create_vein_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         open_pt = actions.find_open_around(world, self.get_position(),
            self.get_resource_distance())
         if open_pt:
            ore = actions.create_ore(world,
               "ore - " + self.get_name() + " - " + str(current_ticks),
               open_pt, current_ticks, i_store)
            world.add_entity(ore)
            tiles = [open_pt]
         else:
            tiles = []

         actions.schedule_action(world, self,
            self.create_vein_action(world, i_store),
            current_ticks + self.get_rate())
         return tiles
      return action
   def create_animation_action(self, world, repeat_count):
      def action(current_ticks):
         self.remove_pending_action(action)

         self.next_image()

         if repeat_count != 1:
            actions.schedule_action(world, self,
               self.create_animation_action(world, max(repeat_count - 1, 0)),
               current_ticks + self.get_animation_rate())

         return [self.get_position()]
      return action

class Ore(Action_Entity):
   def __init__(self, name, position, imgs, rate=5000):
      super(Ore, self).__init__(name, position, imgs)
      self.position = position
      self.rate = rate

   def get_rate(self):
      return self.rate
   def entity_string(self):
      return ' '.join(['ore', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.rate)])
   def create_ore_transform_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)
         blob = actions.create_blob(world, self.get_name() + " -- blob",
            self.get_position(),
            self.get_rate() // BLOB_RATE_SCALE,
            current_ticks, i_store)

         self.remove_entity(world)
         world.add_entity(blob)

         return [blob.get_position()]
      return action

class Blacksmith(Action_Entity):
   def __init__(self, name, position, imgs, resource_limit, rate,
      resource_distance=1):
      super(Blacksmith, self).__init__(name, position, imgs)
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.rate = rate
      self.resource_distance = resource_distance

   def get_rate(self):
      return self.rate
   def set_resource_count(self, n):
      self.resource_count = n
   def get_resource_count(self):
      return self.resource_count
   def get_resource_limit(self):
      return self.resource_limit
   def get_resource_distance(self):
      return self.resource_distance
   def entity_string(self):
      return ' '.join(['blacksmith', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.resource_distance)])
   
class Animated_Entities(Action_Entity):
   def __init__(self, name, position, imgs, animation_rate):
       super(Animated_Entities, self).__init__(name, position, imgs)
       self.animation_rate = animation_rate

   def get_animation_rate(self):
       return self.animation_rate

class OreBlob(Animated_Entities):
   def __init__(self, name, position, rate, imgs, animation_rate):
      super(OreBlob, self).__init__(name, position, imgs, animation_rate)
      self.rate = rate

   def get_rate(self):
      return self.rate
   def entity_string(self):
      return 'unknown'
   def blob_to_vein(self, world, vein):
      entity_pt = self.get_position()
      if not vein:
         return ([entity_pt], False)
      vein_pt = vein.get_position()
      if entity_pt.adjacent(vein_pt):
         vein.remove_entity(world)
         return ([vein_pt], True)
      else:
         new_pt = actions.blob_next_position(world, entity_pt, vein_pt)
         old_entity = world.get_tile_occupant(new_pt)
         if isinstance(old_entity, Ore):
            old_entity.remove_entity(world)
         return (world.move_entity(self, new_pt), False)
   def create_ore_blob_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         vein = world.find_nearest(entity_pt, Vein)
         (tiles, found) = self.blob_to_vein(world, vein)

         next_time = current_ticks + self.get_rate()
         if found:
            quake = actions.create_quake(world, tiles[0], current_ticks, i_store)
            world.add_entity(quake)
            next_time = current_ticks + self.get_rate() * 2

         actions.schedule_action(world, self,
            self.create_ore_blob_action(world, i_store),
            next_time)

         return tiles
      return action
   def create_animation_action(self, world, repeat_count):
      def action(current_ticks):
         self.remove_pending_action(action)

         self.next_image()

         if repeat_count != 1:
            actions.schedule_action(world, self,
               self.create_animation_action(world, max(repeat_count - 1, 0)),
               current_ticks + self.get_animation_rate())

         return [self.get_position()]
      return action

class Quake(Animated_Entities):
   def __init__(self, name, position, imgs, animation_rate):
      super(Quake, self).__init__(name, position, imgs, animation_rate)

   def entity_string(self):
      return 'unknown'
   def create_animation_action(self, world, repeat_count):
      def action(current_ticks):
         self.remove_pending_action(action)

         self.next_image()

         if repeat_count != 1:
            actions.schedule_action(world, self,
               self.create_animation_action(world, max(repeat_count - 1, 0)),
               current_ticks + self.get_animation_rate())

         return [self.get_position()]
      return action
   def create_entity_death_action(self, world):
      def action(current_ticks):
         self.remove_pending_action(action)
         pt = self.get_position()
         self.remove_entity(world)
         return [pt]
      return action


class Miner(Animated_Entities):
   def __init__(self, name, resource_limit, position, rate, imgs,
      animation_rate):
      super(Miner, self).__init__(name, position, imgs, animation_rate)
      self.rate = rate
      self.resource_limit = resource_limit

   def get_rate(self):
      return self.rate
   def set_resource_count(self, n):
      self.resource_count = n
   def get_resource_count(self):
      return self.resource_count
   def get_resource_limit(self):
      return self.resource_limit
   def try_transform_miner(self, world, transform):
      new_entity = transform(world)
      if self != new_entity:
         actions.clear_pending_actions(world, self)
         world.remove_entity_at(self.get_position())
         world.add_entity(new_entity)
         actions.schedule_animation(world, new_entity)
      return new_entity
   def create_animation_action(self, world, repeat_count):
      def action(current_ticks):
         self.remove_pending_action(action)

         self.next_image()

         if repeat_count != 1:
            actions.schedule_action(world, self,
               self.create_animation_action(world, max(repeat_count - 1, 0)),
               current_ticks + self.get_animation_rate())

         return [self.get_position()]
      return action

class MinerNotFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs, animation_rate):
      super(MinerNotFull, self).__init__(name, resource_limit, position, rate, imgs,
         animation_rate)
      self.resource_count = 0

   def entity_string(self):
      return ' '.join(['miner', entity.name, str(entity.position.x),
         str(entity.position.y), str(entity.resource_limit),
         str(entity.rate), str(entity.animation_rate)])
   def miner_to_ore(self, world, ore):
      entity_pt = self.get_position()
      if not ore:
         return ([entity_pt], False)
      ore_pt = ore.get_position()
      if entity_pt.adjacent(ore_pt):
         self.set_resource_count(
            1 + self.get_resource_count())
         ore.remove_entity(world)
         return ([ore_pt], True)
      else:
         new_pt = actions.next_position(world, entity_pt, ore_pt)
         return (world.move_entity(self, new_pt), False)
   def create_miner_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         ore = world.find_nearest(entity_pt, Ore)
         (tiles, found) = self.miner_to_ore(world, ore)

         new_entity = self
         if found:
            new_entity = self.try_transform_miner(world,
               self.try_transform_miner_not_full)

         actions.schedule_action(world, new_entity,
            new_entity.create_miner_action(world, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action
   def try_transform_miner_not_full(self, world):
      if self.resource_count < self.resource_limit:
         return self
      else:
         new_entity = MinerFull(
            self.get_name(), self.get_resource_limit(),
            self.get_position(), self.get_rate(),
            self.get_images(), self.get_animation_rate())
         return new_entity


class MinerFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs, animation_rate):
      super(MinerFull, self).__init__(name, resource_limit, position, rate, imgs,
         animation_rate)
      self.resource_count = resource_limit
   def entity_string(self):
      return 'unknown'
   def miner_to_smith(self, world, smith):
      entity_pt = self.get_position()
      if not smith:
         return ([entity_pt], False)
      smith_pt = smith.get_position()
      if entity_pt.adjacent(smith_pt):
         smith.set_resource_count(
            smith.get_resource_count() +
            self.get_resource_count())
         self.set_resource_count(0)
         return ([], True)
      else:
         new_pt = actions.next_position(world, entity_pt, smith_pt)
         return (world.move_entity(self, new_pt), False)
   def create_miner_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         smith = world.find_nearest(entity_pt, Blacksmith)
         (tiles, found) = self.miner_to_smith(world, smith)

         new_entity = self
         if found:
            new_entity = self.try_transform_miner(world,
               self.try_transform_miner_full)

         actions.schedule_action(world, new_entity,
            new_entity.create_miner_action(world, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action
   def try_transform_miner_full(self, world):
      new_entity = MinerNotFull(
      self.get_name(), self.get_resource_limit(),
      self.get_position(), self.get_rate(),
      self.get_images(), self.get_animation_rate())

      return new_entity