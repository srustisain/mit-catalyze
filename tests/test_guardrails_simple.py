#!/usr/bin/env python3
import asyncio
from src.agents.intent_classifier import IntentClassifier

async def test():
    c = IntentClassifier()
    result = await c.classify('What is the molecular weight of caffeine?')
    print(f'Result: {result.intent.value} - {result.reasoning}')

if __name__ == "__main__":
    asyncio.run(test())
