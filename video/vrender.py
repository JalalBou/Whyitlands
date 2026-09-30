import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1080})
        await pg.goto('http://localhost:8768/_video-tmp.html'); await pg.wait_for_timeout(800)
        for f in range(1800):
            await pg.evaluate(f'render({f/30})')
            await pg.screenshot(path=f'video/frames/{f:05d}.jpg',type='jpeg',quality=93)
        await b.close()
asyncio.run(main())
