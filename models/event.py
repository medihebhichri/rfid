class Event:
    def __init__(self, evenement_id, type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id):
        self.evenement_id = evenement_id
        self.type_evenement = type_evenement
        self.date_evenement = date_evenement
        self.description = description
        self.rfid = rfid
        self.equipe_id = equipe_id
        self.poste_id = poste_id
        self.alerte_id = alerte_id
        self.date_id = date_id