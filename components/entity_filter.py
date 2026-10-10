"""Discard conflicting entity spans; admission facts still validate in the SDK.

This component preserves exact catalogue names and constrains numeric/subject
entities to their relevant intents. It does not manufacture a major from fuzzy text.
"""
from typing import List

from rasa.engine.graph import GraphComponent
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.shared.nlu.training_data.message import Message

from actions.repository import load_catalog


from actions.entities import filter_entities


@DefaultV1Recipe.register(DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR, is_trainable=False)
class AdmissionsEntityFilter(GraphComponent):
    def __init__(self):
        self.catalog = load_catalog()

    @classmethod
    def create(cls, config, model_storage, resource, execution_context):
        return cls()

    def process(self, messages: List[Message]) -> List[Message]:
        for message in messages:
            entities = filter_entities(message.get('text', ''), message.get('intent', {}).get('name'),
                                       message.get('entities', []), self.catalog)
            message.set('entities', entities, add_to_output=True)
        return messages
