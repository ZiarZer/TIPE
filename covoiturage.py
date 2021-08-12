#:import MapView kivy.garden.mapview.MapView

<CarteDemandesPage>:
	lat: 16.250125
	lon: -61.523095
	zoom: 10

	on_zoom:
		self.zoom = 10 if self.zoom < 10 else self.zoom
	on_lat:
		self.lancer_chrono()
	on_lon:
		self.lancer_chrono()

	AnchorLayout:
		anchor_x: 'right'
		anchor_y: 'top'
		Button:
			text: '<| Retour'
			on_release: root.retour_menu_demandes()