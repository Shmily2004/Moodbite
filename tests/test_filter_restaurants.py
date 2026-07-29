import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.filter_restaurants import filter_restaurant_items


class FilterRestaurantItemsTest(unittest.TestCase):
    def test_filters_only_food_related_places(self):
        xml_content = """<?xml version='1.0' encoding='UTF-8'?>
<items>
  <item>
    <title>Nhà hàng Long Hòa</title>
    <categoryName>Nhà hàng</categoryName>
    <categories>Nhà hàng</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
  <item>
    <title>Khách sạn ABC</title>
    <categoryName>Khách sạn</categoryName>
    <categories>Khách sạn</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
  <item>
    <title>Cửa hàng tạp hóa Minh Anh</title>
    <categoryName>Cửa hàng</categoryName>
    <categories>Cửa hàng</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
  <item>
    <title>Quán ăn Phở 24</title>
    <categoryName>Quán ăn</categoryName>
    <categories>Quán ăn</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
</items>"""

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "sample.xml"
            xml_path.write_text(xml_content, encoding="utf-8")

            filtered = filter_restaurant_items(xml_path)

        self.assertEqual([item["title"] for item in filtered], ["Nhà hàng Long Hòa", "Quán ăn Phở 24"])

    def test_excludes_supplier_and_company_like_entries(self):
        xml_content = """<?xml version='1.0' encoding='UTF-8'?>
<items>
  <item>
    <title>Công Ty Tnhh Đầu Tư Kinh Doanh &amp; Thương Mại Vinh Khang Food</title>
    <categoryName>Người cung cấp thực phẩm</categoryName>
    <categories>Người cung cấp thực phẩm</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
  <item>
    <title>Thành Phượng Vietteltelecom</title>
    <categoryName>Chi nhánh Viettel</categoryName>
    <categories>Chi nhánh Viettel</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
  <item>
    <title>Quán ăn Phở Bờ Hồ</title>
    <categoryName>Nhà hàng</categoryName>
    <categories>Nhà hàng</categories>
    <address>Hà Nội</address>
    <location><lat>10</lat><lng>20</lng></location>
  </item>
</items>"""

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "sample.xml"
            xml_path.write_text(xml_content, encoding="utf-8")

            filtered = filter_restaurant_items(xml_path)

        self.assertEqual([item["title"] for item in filtered], ["Quán ăn Phở Bờ Hồ"])


if __name__ == "__main__":
    unittest.main()
