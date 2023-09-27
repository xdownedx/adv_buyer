import re

def markdown_to_text(markdown_string: str) -> str:
    # Удаление ссылок
    markdown_string = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', markdown_string)

    # Удаление жирного текста, курсива и других символов маркдауна
    markdown_string = re.sub(r'\*\*|\*|_|#', '', markdown_string)

    # Удаление изображений
    markdown_string = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', '', markdown_string)

    # Удаление HTML тегов (если они присутствуют)
    markdown_string = re.sub(r'<[^>]+>', '', markdown_string)

    return markdown_string