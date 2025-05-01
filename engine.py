import pygame
import sys
import time
from typing import List, Dict, Tuple, Callable, Any, Optional, Union
import math
import random

class Vector2:
    """A simple 2D vector class with basic operations."""
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return self / mag
        return Vector2(0, 0)
    
    def distance_to(self, other):
        return (other - self).magnitude()
    
    def tuple(self):
        return (self.x, self.y)


class GameObject:
    """Base class for all game objects."""
    def __init__(self, position: Vector2, tag: str = ""):
        self.position = position
        self.rotation = 0.0  # degrees
        self.scale = Vector2(1.0, 1.0)
        self.active = True
        self.tag = tag
        self.components = []
    
    def update(self, delta_time: float):
        """Update this object and all its components."""
        if not self.active:
            return
        
        for component in self.components:
            if component.enabled:
                component.update(delta_time)
    
    def render(self, surface):
        """Render this object and all its components."""
        if not self.active:
            return
        
        for component in self.components:
            if component.enabled:
                component.render(surface)
    
    def add_component(self, component):
        """Add a component to this game object."""
        component.game_object = self
        self.components.append(component)
        return component
    
    def get_component(self, component_type):
        """Get the first component of the specified type."""
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None


class Component:
    """Base class for all components that can be attached to GameObjects."""
    def __init__(self):
        self.game_object = None
        self.enabled = True
    
    def update(self, delta_time: float):
        """Update logic for this component."""
        pass
    
    def render(self, surface):
        """Rendering logic for this component."""
        pass


class SpriteRenderer(Component):
    """Component to render a sprite."""
    def __init__(self, image_path: str = None, color: Tuple[int, int, int] = None, 
                 width: int = 0, height: int = 0):
        super().__init__()
        self.image = None
        self.color = color
        self.width = width
        self.height = height
        
        if image_path:
            self.load_image(image_path)
    
    def load_image(self, image_path: str):
        """Load an image from a file path."""
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.width = self.image.get_width()
            self.height = self.image.get_height()
        except pygame.error:
            print(f"Could not load image: {image_path}")
            # Create a placeholder texture
            self.image = pygame.Surface((32, 32))
            self.image.fill((255, 0, 255))  # Magenta for missing textures
            self.width = 32
            self.height = 32
    
    def render(self, surface):
        """Render the sprite to the surface."""
        if not self.enabled:
            return
        
        if self.image:
            # Scale the image
            scaled_image = pygame.transform.scale(
                self.image, 
                (int(self.width * self.game_object.scale.x), 
                int(self.height * self.game_object.scale.y))
            )
            
            # Rotate the image
            if self.game_object.rotation != 0:
                scaled_image = pygame.transform.rotate(scaled_image, -self.game_object.rotation)
            
            # Get the rect for positioning
            rect = scaled_image.get_rect()
            rect.center = (int(self.game_object.position.x), int(self.game_object.position.y))
            
            # Draw the image
            surface.blit(scaled_image, rect)
        elif self.color and self.width > 0 and self.height > 0:
            # Draw a colored rectangle
            rect = pygame.Rect(
                int(self.game_object.position.x - (self.width * self.game_object.scale.x) / 2),
                int(self.game_object.position.y - (self.height * self.game_object.scale.y) / 2),
                int(self.width * self.game_object.scale.x),
                int(self.height * self.game_object.scale.y)
            )
            
            if self.game_object.rotation == 0:
                pygame.draw.rect(surface, self.color, rect)
            else:
                # For rotated rectangles, we create a surface, draw the rect, rotate it, then blit
                temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(temp_surface, self.color, temp_surface.get_rect())
                rotated_surface = pygame.transform.rotate(temp_surface, -self.game_object.rotation)
                rot_rect = rotated_surface.get_rect(center=rect.center)
                surface.blit(rotated_surface, rot_rect)


class RigidBody(Component):
    """Component for physics simulation."""
    def __init__(self, mass: float = 1.0, gravity: float = 9.8):
        super().__init__()
        self.mass = mass
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.gravity_scale = 1.0
        self.gravity = gravity
        self.use_gravity = True
        self.drag = 0.1  # Air resistance
        self.kinematic = False  # If true, not affected by forces
    
    def apply_force(self, force: Vector2):
        """Apply a force to this rigidbody."""
        if self.kinematic:
            return
        
        # F = ma, so a = F/m
        self.acceleration += force / self.mass
    
    def update(self, delta_time: float):
        """Update physics simulation."""
        if not self.enabled or self.kinematic:
            return
        
        # Apply gravity
        if self.use_gravity:
            self.apply_force(Vector2(0, self.gravity * self.gravity_scale * self.mass))
        
        # Update velocity based on acceleration
        self.velocity += self.acceleration * delta_time
        
        # Apply drag
        self.velocity *= (1 - self.drag * delta_time)
        
        # Update position based on velocity
        self.game_object.position += self.velocity * delta_time
        
        # Reset acceleration
        self.acceleration = Vector2(0, 0)


class Collider(Component):
    """Base collider component."""
    def __init__(self):
        super().__init__()
        self.is_trigger = False
        self.center_offset = Vector2(0, 0)
    
    def is_colliding(self, other) -> bool:
        """Check if this collider is colliding with another."""
        return False
    
    def get_bounds(self):
        """Get the bounds of this collider."""
        return None


class BoxCollider(Collider):
    """Rectangular collision detection."""
    def __init__(self, width: float, height: float):
        super().__init__()
        self.width = width
        self.height = height
    
    def get_bounds(self):
        """Get the bounds rectangle."""
        pos = self.game_object.position + self.center_offset
        half_width = (self.width * self.game_object.scale.x) / 2
        half_height = (self.height * self.game_object.scale.y) / 2
        
        return pygame.Rect(
            int(pos.x - half_width),
            int(pos.y - half_height),
            int(self.width * self.game_object.scale.x),
            int(self.height * self.game_object.scale.y)
        )
    
    def is_colliding(self, other):
        """Check if this box collider is colliding with another collider."""
        if isinstance(other, BoxCollider):
            return self.get_bounds().colliderect(other.get_bounds())
        elif isinstance(other, CircleCollider):
            # Box-circle collision
            rect = self.get_bounds()
            circle_pos = other.game_object.position + other.center_offset
            
            # Find the closest point on the rectangle to the circle
            closest_x = max(rect.left, min(circle_pos.x, rect.right))
            closest_y = max(rect.top, min(circle_pos.y, rect.bottom))
            
            # Calculate the distance between the closest point and the circle center
            distance = Vector2(closest_x, closest_y).distance_to(circle_pos)
            
            return distance < other.radius * max(other.game_object.scale.x, other.game_object.scale.y)
        
        return False


class CircleCollider(Collider):
    """Circular collision detection."""
    def __init__(self, radius: float):
        super().__init__()
        self.radius = radius
    
    def get_bounds(self):
        """Get the bounds rectangle."""
        pos = self.game_object.position + self.center_offset
        scaled_radius = self.radius * max(self.game_object.scale.x, self.game_object.scale.y)
        
        return pygame.Rect(
            int(pos.x - scaled_radius),
            int(pos.y - scaled_radius),
            int(scaled_radius * 2),
            int(scaled_radius * 2)
        )
    
    def is_colliding(self, other):
        """Check if this circle collider is colliding with another collider."""
        if isinstance(other, CircleCollider):
            # Circle-circle collision
            pos1 = self.game_object.position + self.center_offset
            pos2 = other.game_object.position + other.center_offset
            
            radius1 = self.radius * max(self.game_object.scale.x, self.game_object.scale.y)
            radius2 = other.radius * max(other.game_object.scale.x, other.game_object.scale.y)
            
            return pos1.distance_to(pos2) < radius1 + radius2
        elif isinstance(other, BoxCollider):
            # Circle-box collision (use the implementation from BoxCollider)
            return other.is_colliding(self)
        
        return False


class Input:
    """Static class to handle input."""
    _keys_pressed = {}
    _keys_down = set()
    _keys_up = set()
    _mouse_position = Vector2(0, 0)
    _mouse_buttons_pressed = [False, False, False]  # Left, Middle, Right
    _mouse_buttons_down = [False, False, False]
    _mouse_buttons_up = [False, False, False]
    
    @staticmethod
    def update():
        """Update input state."""
        Input._keys_down.clear()
        Input._keys_up.clear()
        Input._mouse_buttons_down = [False, False, False]
        Input._mouse_buttons_up = [False, False, False]
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key not in Input._keys_pressed or not Input._keys_pressed[event.key]:
                    Input._keys_down.add(event.key)
                Input._keys_pressed[event.key] = True
            elif event.type == pygame.KEYUP:
                Input._keys_pressed[event.key] = False
                Input._keys_up.add(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button <= 3:
                    Input._mouse_buttons_pressed[event.button - 1] = True
                    Input._mouse_buttons_down[event.button - 1] = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button <= 3:
                    Input._mouse_buttons_pressed[event.button - 1] = False
                    Input._mouse_buttons_up[event.button - 1] = True
        
        # Update mouse position
        mouse_pos = pygame.mouse.get_pos()
        Input._mouse_position = Vector2(mouse_pos[0], mouse_pos[1])
        
        return True
    
    @staticmethod
    def get_key(key_code):
        """Check if a key is currently pressed."""
        return key_code in Input._keys_pressed and Input._keys_pressed[key_code]
    
    @staticmethod
    def get_key_down(key_code):
        """Check if a key was pressed this frame."""
        return key_code in Input._keys_down
    
    @staticmethod
    def get_key_up(key_code):
        """Check if a key was released this frame."""
        return key_code in Input._keys_up
    
    @staticmethod
    def get_mouse_button(button):
        """Check if a mouse button is currently pressed."""
        if button < 0 or button > 2:
            return False
        return Input._mouse_buttons_pressed[button]
    
    @staticmethod
    def get_mouse_button_down(button):
        """Check if a mouse button was pressed this frame."""
        if button < 0 or button > 2:
            return False
        return Input._mouse_buttons_down[button]
    
    @staticmethod
    def get_mouse_button_up(button):
        """Check if a mouse button was released this frame."""
        if button < 0 or button > 2:
            return False
        return Input._mouse_buttons_up[button]
    
    @staticmethod
    def get_mouse_position():
        """Get the current mouse position."""
        return Input._mouse_position


class Scene:
    """Container for game objects in a level."""
    def __init__(self, name: str = "Untitled Scene"):
        self.name = name
        self.game_objects = []
    
    def add_game_object(self, game_object: GameObject):
        """Add a game object to the scene."""
        self.game_objects.append(game_object)
        return game_object
    
    def remove_game_object(self, game_object: GameObject):
        """Remove a game object from the scene."""
        if game_object in self.game_objects:
            self.game_objects.remove(game_object)
    
    def update(self, delta_time: float):
        """Update all game objects in the scene."""
        for game_object in self.game_objects:
            game_object.update(delta_time)
    
    def render(self, surface):
        """Render all game objects in the scene."""
        for game_object in self.game_objects:
            game_object.render(surface)
    
    def find_game_object_by_tag(self, tag: str):
        """Find the first game object with the specified tag."""
        for game_object in self.game_objects:
            if game_object.tag == tag:
                return game_object
        return None
    
    def find_game_objects_by_tag(self, tag: str):
        """Find all game objects with the specified tag."""
        return [obj for obj in self.game_objects if obj.tag == tag]


class Game:
    """The main game class."""
    def __init__(self, title: str, width: int, height: int, fps: int = 60):
        pygame.init()
        self.title = title
        self.width = width
        self.height = height
        self.target_fps = fps
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = False
        self.current_scene = None
        self.scenes = {}
        self.delta_time = 0
    
    def add_scene(self, scene: Scene):
        """Add a scene to the game."""
        self.scenes[scene.name] = scene
        if self.current_scene is None:
            self.current_scene = scene
    
    def load_scene(self, scene_name: str):
        """Load a scene by name."""
        if scene_name in self.scenes:
            self.current_scene = self.scenes[scene_name]
        else:
            print(f"Scene '{scene_name}' not found.")
    
    def run(self):
        """Run the game loop."""
        self.running = True
        
        while self.running:
            # Calculate delta time
            self.delta_time = self.clock.tick(self.target_fps) / 1000.0
            
            # Update input
            self.running = Input.update()
            
            # Update the current scene
            if self.current_scene:
                self.current_scene.update(self.delta_time)
            
            # Clear the screen
            self.screen.fill((0, 0, 0))
            
            # Render the current scene
            if self.current_scene:
                self.current_scene.render(self.screen)
            
            # Flip the display
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


# Example usage
if __name__ == "__main__":
    # Create the game
    game = Game("Simple Game Engine Demo", 800, 600)
    
    # Create a scene
    main_scene = Scene("Main")
    
    # Create a player object
    player = GameObject(Vector2(400, 300), "player")
    
    # Add a sprite renderer component
    sprite = player.add_component(SpriteRenderer(color=(0, 255, 0), width=50, height=50))
    
    # Add physics
    rigidbody = player.add_component(RigidBody())
    rigidbody.use_gravity = False
    
    # Add a collider
    collider = player.add_component(BoxCollider(50, 50))
    
    # Add player to the scene
    main_scene.add_game_object(player)
    
    # Create some obstacles
    for i in range(5):
        obstacle = GameObject(Vector2(random.randint(100, 700), random.randint(100, 500)), "obstacle")
        obstacle.add_component(SpriteRenderer(color=(255, 0, 0), width=30, height=30))
        obstacle.add_component(BoxCollider(30, 30))
        main_scene.add_game_object(obstacle)
    
    # Add scene to the game
    game.add_scene(main_scene)
    
    # Define a player controller component
    class PlayerController(Component):
        def __init__(self, speed: float = 200.0):
            super().__init__()
            self.speed = speed
        
        def update(self, delta_time: float):
            # Get player input
            x_input = 0
            y_input = 0
            
            if Input.get_key(pygame.K_a) or Input.get_key(pygame.K_LEFT):
                x_input -= 1
            if Input.get_key(pygame.K_d) or Input.get_key(pygame.K_RIGHT):
                x_input += 1
            if Input.get_key(pygame.K_w) or Input.get_key(pygame.K_UP):
                y_input -= 1
            if Input.get_key(pygame.K_s) or Input.get_key(pygame.K_DOWN):
                y_input += 1
            
            # Normalize input vector for consistent speed in all directions
            if x_input != 0 or y_input != 0:
                move_dir = Vector2(x_input, y_input).normalize()
                
                # Get the rigidbody component
                rb = self.game_object.get_component(RigidBody)
                if rb:
                    # Apply movement force
                    rb.velocity = move_dir * self.speed
            
            # Check collisions with obstacles
            player_collider = self.game_object.get_component(BoxCollider)
            if player_collider:
                for obstacle in main_scene.find_game_objects_by_tag("obstacle"):
                    obstacle_collider = obstacle.get_component(BoxCollider)
                    if obstacle_collider and player_collider.is_colliding(obstacle_collider):
                        # Change color on collision
                        obstacle_renderer = obstacle.get_component(SpriteRenderer)
                        if obstacle_renderer:
                            obstacle_renderer.color = (0, 0, 255)
    
    # Add the player controller component to the player
    player.add_component(PlayerController(300.0))
    
    # Run the game
    game.run()
