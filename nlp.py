from collections import Counter
from string import punctuation
import spacy
import pytextrank
import yake
# nlp = spacy.load("en_core_web_sm")
# doc = nlp("This is a sentence.")

# doc = nlp("You can distinguish a Cream French Bulldog from its Fawn counterpart by noticing the whiter, less yellow-tanned hue of the former and its lack of sharp color patterns. The AKC recognizes this as one of nine official colors for French Bulldogs. Common black masks are seen in both Cream and Fawn Frenchie breeds, which adds to confusion between them.")


class NLP:

    class CustomException(Exception):
        def __init__(self, message):
            self.message = message

        def getJSON(self):
            if type(self.message) is dict:
                return self.message
            return {'error': self.message, "success": False}

        def __str__(self):
            return self.getJSON()['message']

    def __init__(self, model="en_core_web_lg"):
        self.model = None
        self.set_model(model)
        self.kw_extractor = yake.KeywordExtractor(top=30)

    def set_model(self, model):
        if not model or model == self.model:
            return None
        self.model = model
        self.nlp = spacy.load(self.model)
        # self.nlp.add_pipe("textrank")

    def get_sentences(self, text):
        doc = self.nlp(text)
        sentences = []
        for sent in doc.sents:
            sentences.append({"text": sent.text})
        return sentences

    def get_entities(self, text):
        doc = self.nlp(text)
        ents = []
        for ent in doc.ents:
            # print(ent.text, ent.label_)
            ents.append({"text": ent.text, "label": ent.label_})
        return ents

    def get_noun_chunks(self, text):
        doc = self.nlp(text)
        noun_chunks = []
        for noun_chunk in doc.noun_chunks:
            noun_chunks.append(
                {"text": noun_chunk.text, "label": noun_chunk.label_})
        return noun_chunks

    def get_keywords2(self, text):
        result = []
        pos_tag = ['PROPN', 'ADJ', 'NOUN']
        doc = self.nlp(text.lower())
        for token in doc:
            if (token.text in self.nlp.Defaults.stop_words or token.text in punctuation):
                continue
            if (token.pos_ in pos_tag):
                result.append(token.text)
        return result

    def get_keywords(self, text):
        result = []
        keywords = self.kw_extractor.extract_keywords(text)
        for kw in keywords:
            result.append({"keyword": kw[0], "score": kw[1]})
        return result

    def call(self, args):
        model = args.get("model", None)
        get = args.get("get", "entities")
        text = args.get("text", None)
        if text is None:
            raise self.CustomException("No text provided")
        self.set_model(model)
        match get:
            case "sentences":
                d = self.get_sentences(text)
            case "keywords":
                d = self.get_keywords(text)
            case _:
                d = self.get_entities(text)
        return {"success": True, "data": d}


# nlp = NLP()
# txt = "You can distinguish a Cream French Bulldog from its Fawn counterpart by noticing the whiter, less yellow-tanned hue of the former and its lack of sharp color patterns. The AKC recognizes this as one of nine official colors for French Bulldogs. Common black masks are seen in both Cream and Fawn Frenchie breeds, which adds to confusion between them."
# print(nlp.get_keywords(txt))
