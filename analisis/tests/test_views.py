from django.test import TestCase
from django.urls import reverse


class AnalisisViewsTests(TestCase):
    def test_index_renderiza_con_canvases_y_filtros(self):
        url = reverse("analisis:index")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn("Patrones de consumo", html)
        self.assertIn('name="desde"', html)
        self.assertIn('name="hasta"', html)

        self.assertIn('id="chartLine"', html)
        self.assertIn('id="chartTop"', html)
        self.assertIn('id="chartPie"', html)
        
        self.assertIn('data-bs-toggle="offcanvas"', html)