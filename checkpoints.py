CHECKPOINTS = [
	("Anse-Bertrand", 16.473323, -61.50686),
	("Baie-Mahault", 16.250906, -61.588866),
	("Baillif", 16.022827, -61.746107),
	("Basse-Terre", 15.991794, -61.729251),
	("Bouillante", 16.172579, -61.776301),
	("Deshaies", 16.32077, -61.786697),
	("Capesterre-Belle-Eau", 16.053753, -61.567821),
	("Gourbeyre", 15.994605, -61.693643),
	("Goyave", 16.132876, -61.58033),
	("Lamentin", 16.26335, -61.641754),
	("Le Gosier", 16.208616, -61.469865),
	("Le Moule", 16.334102, -61.34956),
	("Les Abymes", 16.263672, -61.512763),
	("Morne-à-l-eau", 16.331226, -61.458004),
	("Petit-Bourg", 16.201661, -61.605726),
	("Petit-Canal", 16.3832, -61.484828),
	("Pointe-à-Pitre", 16.250708, -61.527754),
	("Pointe-Noire", 16.232369, -61.789663),
	("Port-Louis", 16.418337, -61.5258432),
	("Saint-Claude", 16.02536, -61.6998215),
	("Saint-François", 16.257283, -61.275463),
	("Sainte-Anne", 16.223701, -61.389252),
	("Sainte-Rose", 16.332137, -61.696234),
	("Trois-Rivières", 15.98119, -61.625871),
	("Vieux-Habitant", 16.058243, -61.764807),
	("Vieux-Fort", 15.950987, -61.704894)
]


def distance_carre(lat, lon, checkpoint):
    #checkpoint est de la forme (nom_du_checkpoint, lat, lon)
    LAT_checkpoint, LON_checkpoint = checkpoint[1], checkpoint[2]
    return (LAT_checkpoint - lat)**2 + (LON_checkpoint - lon)**2

def plus_proche_checkpoint(lat, lon):
    distance_min, indice_plus_proche = distance_carre(lat, lon, CHECKPOINTS[0]), 0

    for k in range(1, len(CHECKPOINTS)):
        dist_checkpoint = distance_carre(lat, lon, CHECKPOINTS[k])
        
        if dist_checkpoint<distance_min:
            distance_min, indice_plus_proche = dist_checkpoint, k

    return CHECKPOINTS[indice_plus_proche]

def coordonnees_checkpoint(nom):
	for checkpoint in CHECKPOINTS:
		if checkpoint[0]==nom:
			return (checkpoint[1], checkpoint[2])