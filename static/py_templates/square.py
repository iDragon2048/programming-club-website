import pygame
import asyncio

pygame.init()
screen = pygame.display.set_mode((400, 300))
clock = pygame.time.Clock()

async def main():
    x, y, size, speed = 175, 125, 50, 5
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: y += speed

        x = max(0, min(x, 400 - size))
        y = max(0, min(y, 300 - size))

        screen.fill((40, 40, 40))
        pygame.draw.rect(screen, (0, 255, 150), (x, y, size, size))
        pygame.display.flip()

        clock.tick(60)
        await asyncio.sleep(0)

await main()