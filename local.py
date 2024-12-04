from icd_api.icd_api import Api
from scripts.get_all_entities import get_entities_recurse, get_all_entities

api = Api.from_environment()
root_entity_id = "MMS"
output_folder = "./output"

# print(api.get_entity(entity_id="455013390"))
# print(api.search_entities(search_string="condition"))
# print(api.lookup(entity_id="1944385475"))
# print(api.get_code(code="8A01", icd_version="11"))

get_all_entities()
