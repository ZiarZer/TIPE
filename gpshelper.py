from plyer import gps
from kivy.utils import platform
from kivymd.uix.dialog import MDDialog

class PartageLocalisation():
    def run(self):
        if platform in ('android', 'ios'):

            gps.configure(on_location=self.actualiser_position, on_status=self.verifier_autorisation)
            gps.start(minTime=1000, minDistance=0)

    def actualiser_position(self, *args, **kwargs):
        lat_user = kwargs['lat']
        lon_user = kwargs['lon']


    def verifier_autorisation(self, general_status, status_message):
        if general_status == 'provider-enabled':
            pass
            #Si le GPS est autorisé, on ne fait rien
        else:
            self.popup_demande_activer_gps()

    def popup_demande_activer_gps(self):
        dialog = MDDialog(title="Localisation non partagée", text="Veuillez activer l'accès au GPS")
        dialog.open()