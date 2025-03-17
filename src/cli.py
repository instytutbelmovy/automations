"""
Кансольны інтэрфейс для POS-тагера.
"""

import argparse
import asyncio
from dotenv import load_dotenv

def main():
    """Галоўная функцыя праграмы."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='POS-тагер з выкарыстаннем розных LLM')
    parser.add_argument('input', help='Шлях да ўваходнага файла')
    parser.add_argument('--provider', '-p', 
                       choices=['claude', 'chatgpt', 'gemini'],
                       default='claude',
                       help='Выбар LLM правайдэра')
    
    args = parser.parse_args()
    
    # TODO: Рэалізаваць логіку апрацоўкі

if __name__ == '__main__':
    asyncio.run(main()) 