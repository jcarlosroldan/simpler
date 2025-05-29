from typing import List, Tuple

DBPEDIA_PREFIX = 'PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\nPREFIX : <http://dbpedia.org/resource/>\nPREFIX dbc: <http://dbpedia.org/resource/Category:>\nPREFIX dct: <http://purl.org/dc/terms/>\nPREFIX dbo: <http://dbpedia.org/ontology/>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\n'
QUERY_CLASSES = '''select ?type count (*) as ?num where {
	quad map virtrdf:DefaultQuadMap {
		graph ?g {
			?s1 rdfs:label ?o1 .
			?o1 bif:contains  '"%s"'
		}
	}
	?s1 a ?type .
} group by ?type order by desc 2 limit 100 offset 0'''

def dbpedia(query: str):
	try:
		from SPARQLWrapper import JSON, SPARQLWrapper
	except Exception as e:
		raise RuntimeError('You should call `pip install SPARQLWrapper` before.') from e
	res = SPARQLWrapper('http://dbpedia.org/sparql')
	res.setReturnFormat(JSON)
	res.setQuery(DBPEDIA_PREFIX + query)
	return res.query().convert()['results']['bindings']

def entity_types(value) -> List[Tuple[str, int]]:
	res = dbpedia(QUERY_CLASSES % value.replace(' ', ' AND '))
	return [(r['type']['value'], int(r['num']['value'])) for r in res]