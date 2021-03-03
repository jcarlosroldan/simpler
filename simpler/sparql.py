from SPARQLWrapper import SPARQLWrapper, JSON

DBPEDIA_PREFIX = 'PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\nPREFIX : <http://dbpedia.org/resource/>\nPREFIX dbc: <http://dbpedia.org/resource/Category:>\nPREFIX dct: <http://purl.org/dc/terms/>\nPREFIX dbo: <http://dbpedia.org/ontology/>\n\n'
QUERY_CLASSES = '''select ?type count (*) as ?num where {
    quad map virtrdf:DefaultQuadMap {
        graph ?g {
            ?s1 ?s1textp ?o1 .
            ?o1 bif:contains  '"%s"'
        }
    }
    ?s1 a ?type .
} group by ?type order by desc 2 limit 100 offset 0'''

def dbpedia(query):
    ''' Sends a query to DBPedia and return the results. '''
    res = SPARQLWrapper("http://dbpedia.org/sparql")
    res.setReturnFormat(JSON)
    res.setQuery(DBPEDIA_PREFIX + query)

    return res.query().convert()['results']['bindings']

def entity_types(value):
    ''' Return every entity type with values that contain a given string sorted by frequency.'''
    res = dbpedia(QUERY_CLASSES % value.replace(' ', ' AND '))
    return [(r['type']['value'], int(r['num']['value'])) for r in res]