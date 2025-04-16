# groups.py
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
import pygame

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()

    def draw(self, target_pos):
        """
        target_pos is typically the player's rect.center.
        We'll offset every sprite so that the player is in the screen center.
        """
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2)

        # You can separate objects into different layers, or just draw them.
        # We'll do a small layering: ground vs objects.
        ground_sprites = [sprite for sprite in self if hasattr(sprite, 'ground')]
        object_sprites = [sprite for sprite in self if not hasattr(sprite, 'ground')]

        for layer in [ground_sprites, object_sprites]:
            # Sort them by rect.centery => "simple" layering
            for sprite in sorted(layer, key=lambda s: s.rect.centery):
                offset_pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, offset_pos)
