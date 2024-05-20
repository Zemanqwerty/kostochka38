from .sphinxapi import SphinxClient


def sphinx_search(model_class, query, limits=None, weights=None):
    client = SphinxClient()
    index = str(model_class.objects.model._meta.db_table)
    matches = set()
    original_query = query

    client.SetLimits(0, 1)
    query = client.EscapeString('"%s"' % query)
    result = client.Query(query, index)
    if result is None:
        raise Exception(client.GetLastError())
    elif result['total'] != 0:
        matches.add(result['matches'][0]['id'])

    if limits is not None:
        client.SetLimits(limits[0], limits[1] * 2)
    if weights is not None:
        client.SetFieldWeights(weights)

    result = {'total': 0}
    query = original_query
    query = client.EscapeString(query)
    tokens = query.split(' ')
    while result['total'] == 0 and len(tokens) != 0:
        query = ' '.join(tokens)
        result = client.Query(query, index)
        if result is None:
            raise Exception(client.GetLastError())
        tokens = tokens[:-1]

    for match in result['matches']:
        matches.add(match['id'])
    matches = list(matches)[:limits[1]]

    queryset = model_class.objects.filter(id__in=matches).distinct()
    
    return queryset