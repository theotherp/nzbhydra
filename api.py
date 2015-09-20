# Get dict from object and remove all values that won't be contained in newznab api result
from itertools import groupby
from marshmallow import Schema, fields
from config import cfg


from config import init
init("ResultProcessing.duplicateSizeThreshold", 0.1, float)
init("ResultProcessing.duplicateAgeThreshold", 36000, int)

def get_api_result_as_dicts(search_results):
    dicts = []
    for d in search_results:
        d = d.__dict__
        if "sizeRedable" in d:
            d.pop("sizeRedable")
        dicts.append(d)

    channel = {"title": "todo", "description": "todo", "link": "todo", "language": "todo", "webMaster": "todo", "category": {},  # todo category
               "image": {},  # todo image
               "response": {
                   "@attributes": {  # todo attributes
                                     "offset": "0",
                                     "total": len(dicts)
                                     }
               },
               "item": dicts
               }
    result = {"channel": channel}
    return result


def find_duplicates(results):
    """

    :type results: list[NzbSearchResult]
    """
    # TODO we might want to be able to specify more precisely what item we pick of a group of duplicates, for example by indexer priority 
    uniques = []
    duplicates = []
    # Sort and group by title. We only need to check the items in each individual group against each other because we only consider items with the same title as possible duplicates
    sorted_results = sorted(results, key=lambda x: x.title)
    grouped_by_title = groupby(sorted_results, key=lambda x: x.title)

    for key, group in grouped_by_title:
        seen = set()
        group = list(group)
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if j not in seen:
                    if test_for_duplicate(group[i], group[j]):
                        seen.add(i)
            if i not in seen:
                uniques.append(group[i])
            else:
                duplicates.append(group[i])
    return uniques, duplicates


def test_for_duplicate(search_result_1, search_result_2):
    """

    :type search_result_1: NzbSearchResult
    :type search_result_2: NzbSearchResult
    """
    
    if search_result_1.title != search_result_2.title:
        return False
    size_threshold = cfg.section("ResultProcessing").get("duplicateSizeThresholdInPercent", 0.1)
    age_threshold = cfg.section("ResultProcessing").get("duplicateAgeThreshold", 36000)
    size_difference = search_result_1.size - search_result_2.size
    size_average = (search_result_1.size + search_result_2.size) / 2

    size_difference_percent = abs(size_difference / size_average) * 100
    same_size = size_difference_percent <= size_threshold
    same_age = abs(search_result_1.age - search_result_2.age) <= age_threshold

    # TODO this could probably be more comprehensible but all solutions I found use sets(so hashing) for comparison but we need a "fuzzy" uniqueness check
    # If all nweznab providers would provide poster/group in their infos then this would be a lot easier and more precise
    # We could also use something to combine several values to a score, say that if a two posts have the exact size their age may differe more or combine relative and absolute size comparison
    if same_size and same_age:
        return True


class NzbSearchResultSchema(Schema):
    title = fields.String()
    link = fields.String()
    age = fields.Integer()
    pubDate = fields.String()
    provider = fields.String()
    guid = fields.String()
    size = fields.Integer()
    categories = fields.String()


def process_for_internal_api(results):
    # todo do what ever we need do prepare the results to be shown on our own page instead of being returned as newznab-compatible API
    """

    :type results: list[NzbSearchResult]
    """
    results, duplicates = find_duplicates(results)
    dic_to_return = {"results": serialize_nzb_search_result(results).data, "duplicates": serialize_nzb_search_result(duplicates).data}
    return dic_to_return


def serialize_nzb_search_result(result):
    return NzbSearchResultSchema(many=True).dump(result)
