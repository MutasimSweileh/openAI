from mercury_parser.client import MercuryParser
parser = MercuryParser()
article = parser.parse_article(
    'https://www.dogswiz.com/can-dogs-eat-garlic-butter/')
print(article.json())
