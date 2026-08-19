"""CHẠY MỘT LẦN (2026-08-19): đổi seed món từ THÀNH PHẦN sang GIỚI THIỆU NGẮN.

Chủ dự án chốt bỏ phần nguyên liệu, thay bằng một đoạn giới thiệu ngắn. Script này:
  1. Xoá trường `ingredients` khỏi `dish_seed_manual.json`
  2. Điền `description` soạn tay cho món Wikipedia không có bài (món dân dã, món khái quát)
  3. Đánh dấu `skip_wikipedia` cho món mà bài Wikipedia nói về NGUYÊN LIỆU/CON VẬT chứ
     không phải MÓN ĂN (bài "Ốc" nói về con ốc, bài "Cơm" nói về hạt gạo)

Giữ trong `scripts/legacy/` sau khi chạy để còn truy được vì sao dữ liệu đổi hình dạng.
Chạy lại nhiều lần vẫn an toàn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data_pipeline" / "dish_seed_manual.json"

# Giới thiệu ngắn SOẠN TAY. Mỗi câu nói rõ món đó LÀ GÌ và ăn thế nào.
# KHÔNG bịa nguồn gốc, KHÔNG bịa số liệu - chỉ mô tả thứ ai cũng kiểm chứng được.
INTRO = {
    "bun-ca": "Bún cá là món bún chan nước dùng nấu từ xương và cá, ăn kèm cá rán vàng, thì là và rau cần. Vị thanh, chua nhẹ, hợp bữa sáng và bữa trưa.",
    "bun-oc": "Bún ốc là món bún nước có vị chua đặc trưng từ giấm bỗng, ăn kèm ốc, cà chua và tía tô. Là món quà sáng quen thuộc của Hà Nội.",
    "bun-thit-nuong": "Bún thịt nướng gồm bún tươi ăn cùng thịt lợn nướng than, rau sống, lạc rang và nước mắm chua ngọt chan lên trên. Ăn nguội, không chan nước dùng.",
    "bun-mien-ngan": "Miến ngan là món miến dong chan nước dùng ninh từ xương ngan, ăn kèm thịt ngan và măng. Món nước ấm, hợp bữa sáng.",
    "mien-luon": "Miến lươn là món miến nấu với lươn, có cả kiểu chan nước lẫn kiểu trộn với lươn chiên giòn, rắc hành phi và rau răm.",
    "banh-da-cua": "Bánh đa cua là món nước đặc sản Hải Phòng, dùng sợi bánh đa đỏ chan nước nấu từ gạch cua đồng, ăn kèm chả lá lốt và rau muống.",
    "nem-nuong": "Nem nướng là thịt lợn xay ướp gia vị, nặn viên rồi nướng than, thường cuốn bánh tráng với rau sống và chấm nước sốt đậm vị.",
    "banh-trang-tron": "Bánh tráng trộn là món ăn vặt gồm bánh tráng cắt sợi trộn cùng khô bò, trứng cút, xoài xanh, rau răm và sa tế. Ăn nguội, vị chua cay mặn ngọt.",
    "banh-duc-nong": "Bánh đúc nóng là bột gạo khuấy chín ăn khi còn nóng, chan nước mắm pha, rắc thịt băm xào mộc nhĩ và hành phi.",
    "mi-cay": "Mì cay là món mì nước kiểu Hàn Quốc nấu với kim chi, hải sản và xúc xích, chia theo nhiều cấp độ cay để người ăn tự chọn.",
    "tra-chanh": "Trà chanh là đồ uống pha từ trà, chanh tươi và đường, dùng lạnh. Phổ biến ở quán vỉa hè, hợp ngồi lâu trò chuyện.",
    "sua-chua-tran-chau": "Sữa chua trân châu là món tráng miệng lạnh gồm sữa chua ăn cùng trân châu dai và đá bào, vị chua ngọt mát.",
    "bia-hoi": "Bia hơi là loại bia tươi không tiệt trùng, rót trực tiếp từ keg và uống trong ngày. Gắn liền với quán vỉa hè và các món nhắm bình dân.",
    "lau-nuong": "Lẩu nướng là kiểu ăn vừa nướng thịt trên vỉ vừa nhúng lẩu trên cùng một bàn, thường dành cho nhóm đông vào buổi tối.",
    "goi-cuon": "Gỏi cuốn là món cuốn bằng bánh tráng với tôm, thịt luộc, bún và rau thơm, ăn nguội, chấm tương hoặc nước mắm pha.",
    "com-rang": "Cơm rang là cơm đảo trên chảo nóng cùng trứng, hành và các loại nhân như lạp xưởng hoặc thịt. Món nhanh, no bụng.",
    "chan-ga-nuong": "Chân gà nướng là món ăn vặt buổi tối, chân gà ướp sa tế hoặc mật ong rồi nướng than, ăn nóng.",
    "pho-cuon": "Phở cuốn dùng bánh phở không thái sợi, cuốn cùng thịt bò xào và rau thơm, ăn nguội và chấm nước mắm pha. Món đặc trưng của Hà Nội.",
    "banh-gio": "Bánh giò là bánh bột gạo hấp trong lá chuối, nhân thịt băm và mộc nhĩ, ăn nóng. Món quà sáng rẻ và no.",
    "ga-ran": "Gà rán là thịt gà tẩm bột chiên giòn, thường ăn kèm khoai tây chiên và nước sốt. Phổ biến ở các chuỗi đồ ăn nhanh.",
    "hamburger": "Hamburger là bánh mì tròn kẹp thịt bò nướng, phô mai và rau, ăn bằng tay.",
    "mi-y": "Mì Ý là món mì sợi dài luộc chín, trộn cùng sốt cà chua hoặc sốt kem, thường rắc phô mai bào lên trên.",
    "ramen": "Ramen là món mì nước Nhật Bản với nước dùng ninh kỹ, ăn kèm thịt lợn chashu, trứng lòng đào và rong biển.",
    "kimbap": "Kimbap là món cơm cuộn rong biển kiểu Hàn Quốc với nhân rau củ, trứng và xúc xích, cắt khoanh ăn nguội.",
    "tokbokki": "Tteokbokki là bánh gạo Hàn Quốc xào sốt ớt gochujang, vị cay ngọt, thường ăn kèm chả cá.",
    "dimsum": "Dimsum là tập hợp các món điểm tâm Quảng Đông, phần lớn hấp trong xửng nhỏ, ăn vào bữa sáng hoặc trưa.",
    "vit-quay": "Vịt quay là món vịt tẩm ngũ vị hương rồi quay đến khi da giòn, thường chặt miếng ăn kèm cơm hoặc bánh bao.",
    "tom-yum": "Tom Yum là món canh chua cay Thái Lan nấu với sả, lá chanh, riềng và ớt, thường dùng tôm hoặc hải sản.",
    "salad": "Salad là món rau trộn ăn nguội cùng sốt, thường dùng làm món khai vị hoặc bữa nhẹ ít dầu mỡ.",
    "banh-ngot": "Bánh ngọt là các loại bánh nướng lò có vị ngọt như bánh kem, bánh quy hay bánh mì ngọt, thường ăn kèm trà hoặc cà phê.",
    "ca-phe-sua-da": "Cà phê sữa đá là cà phê pha phin trộn sữa đặc rồi thêm đá, vị đậm và ngọt. Thức uống phổ biến nhất ở quán cà phê Việt Nam.",
    "tra-dao-cam-sa": "Trà đào cam sả là đồ uống lạnh pha từ trà, đào ngâm, cam và sả, vị chua ngọt thơm, thường dùng giải nhiệt.",
    "tra-sua-tran-chau": "Trà sữa trân châu là trà pha sữa dùng lạnh, ăn kèm hạt trân châu dai.",
    "pho-bo": "Phở bò là món phở dùng nước dùng ninh từ xương bò với quế, hồi và gừng nướng, ăn cùng bánh phở và thịt bò thái mỏng.",
    "pho-ga": "Phở gà là món phở dùng nước dùng ninh từ xương gà, ăn cùng thịt gà xé hoặc thái miếng, vị thanh nhẹ hơn phở bò.",
    "bun-nuoc": "Bún nước là cách gọi chung cho các món bún chan nước dùng nóng, ăn kèm rau sống. Nhóm món quen thuộc trong bữa sáng của người Việt.",
    "bun": "Bún là sợi làm từ bột gạo, luộc chín, dùng làm nền cho rất nhiều món Việt như bún chả, bún cá, bún riêu.",
    "mien": "Miến là sợi khô làm từ tinh bột dong hoặc đậu xanh, khi nấu trở nên trong và dai, dùng cho cả món nước lẫn món trộn.",
    "mien-tron": "Miến trộn là món miến không chan nước dùng, trộn cùng thịt, rau thơm và nước trộn chua ngọt.",
    "com": "Cơm là món chính trong bữa ăn Việt, gạo nấu chín ăn cùng các món mặn, canh và rau.",
    "com-hop": "Cơm hộp là suất cơm mang đi gồm cơm, món mặn, rau và canh, phục vụ nhanh cho bữa trưa.",
    "com-chay": "Cơm chay là suất cơm không dùng thịt cá, thay bằng đậu phụ, rau củ và nấm.",
    "com-suon": "Cơm sườn là suất cơm ăn kèm sườn lợn nướng hoặc rim, thường có thêm canh và dưa.",
    "com-ga": "Cơm gà là món cơm nấu cùng nước luộc gà, ăn kèm thịt gà và nước chấm gừng.",
    "com-tam-suon": "Cơm tấm sườn dùng gạo tấm, ăn kèm sườn nướng, bì, chả trứng và nước mắm chua ngọt. Món đặc trưng miền Nam.",
    "do-nham": "Đồ nhắm là các món ăn kèm khi uống bia rượu như lạc rang, nem chua, khô bò hay dưa chuột.",
    "thit-nuong-vi": "Thịt nướng vỉ là thịt ướp gia vị rồi nướng trực tiếp trên vỉ than tại bàn, ăn kèm rau sống và nước chấm.",
    "hai-san-nuong": "Hải sản nướng gồm tôm, mực, sò nướng than, thường phết mỡ hành và chấm muối ớt chanh.",
    "lau-thai": "Lẩu Thái là món lẩu nước chua cay nấu kiểu Thái với sả, lá chanh và riềng, nhúng hải sản và rau.",
    "lau-ga-la-e": "Lẩu gà lá é là món lẩu nấu với thịt gà và lá é, có vị the đặc trưng.",
    "lau-hai-san": "Lẩu hải sản là món lẩu nhúng tôm, mực, ngao cùng rau, ăn kèm bún hoặc mì.",
    "oc-luoc": "Ốc luộc là ốc luộc cùng sả và lá chanh, chấm nước mắm gừng ớt. Món ăn vặt buổi tối rất phổ biến ở Hà Nội.",
    "nem-ran": "Nem rán là món cuốn nhân thịt băm, miến và mộc nhĩ trong bánh đa nem rồi chiên giòn. Miền Nam gọi là chả giò.",
    "nem-chua-ran": "Nem chua rán là nem chua tẩm bột chiên giòn, ăn nóng chấm tương ớt. Món ăn vặt phổ biến.",
    "chao-nong": "Cháo nóng là gạo ninh nhừ với nước dùng, ăn nóng, dễ tiêu. Thường dùng cho bữa sáng hoặc bữa khuya.",
    "banh-cuon-nong": "Bánh cuốn nóng là bột gạo tráng mỏng hấp chín, cuộn nhân thịt băm mộc nhĩ, chấm nước mắm pha.",
    "xoi-man": "Xôi mặn là xôi nếp ăn kèm các món mặn như thịt, chả, trứng hoặc lạp xưởng. Bữa sáng no và tiện mang đi.",
    "xoi": "Xôi là gạo nếp đồ chín bằng hơi nước, có cả loại ngọt lẫn mặn, là món ăn sáng quen thuộc.",
    "banh-mi-thit": "Bánh mì thịt là bánh mì Việt kẹp thịt, pate, rau thơm và đồ chua. Ăn nhanh, cầm tay được.",
    "banh-mi": "Bánh mì là ổ bánh vỏ giòn ruột xốp, dùng để kẹp nhân làm món ăn nhanh đặc trưng của Việt Nam.",
    "pizza": "Pizza là bánh bột nướng lò phủ sốt cà chua, phô mai và các loại nhân, cắt miếng khi ăn.",
    "pizza-hai-san": "Pizza hải sản là pizza phủ tôm, mực và các loại hải sản cùng phô mai.",
    "pizza-pho-mai": "Pizza phô mai là loại pizza cơ bản nhất, chỉ có sốt cà chua và phô mai mozzarella.",
    "bit-tet": "Bít tết là miếng thịt bò áp chảo hoặc nướng, ăn kèm khoai tây và sốt. Ở Việt Nam thường dùng cùng bánh mì.",
    "mi-xao-gion": "Mì xào giòn là mì trứng chiên giòn rồi rưới sốt sánh xào cùng thịt và rau cải.",
    "mi-van-than": "Mì vằn thắn là món mì nước gốc Hoa với sủi cảo, thịt xá xíu, trứng và rau cải.",
    "mi-y-sot-bo-bam": "Mì Ý sốt bò bằm là mì spaghetti ăn cùng sốt cà chua nấu thịt bò băm.",
    "pad-thai": "Pad Thái là món phở xào kiểu Thái với trứng, đậu phộng và me, vị chua ngọt.",
    "sushi": "Sushi là món Nhật gồm cơm trộn giấm ăn kèm hải sản sống hoặc chín, nắn miếng hoặc cuộn rong biển.",
    "burger": "Burger là bánh mì tròn kẹp thịt và rau, ăn bằng tay, phục vụ nhanh.",
    "cha-ca": "Chả cá Lã Vọng là đặc sản Hà Nội: cá tẩm nghệ nướng rồi rán lại với thì là và hành, ăn cùng bún và mắm tôm.",
    "banh-xeo": "Bánh xèo là bánh bột gạo pha nghệ tráng mỏng, nhân tôm thịt và giá, cuốn rau sống chấm nước mắm chua ngọt.",
    "bun-cha": "Bún chả là món Hà Nội gồm chả thịt lợn nướng than thả trong bát nước mắm chua ngọt, ăn kèm bún và rau sống.",
    "bun-bo-hue": "Bún bò Huế là món bún nước cay đặc sản xứ Huế, nước dùng nấu với sả và mắm ruốc, ăn cùng bắp bò và giò heo.",
    "bun-rieu-cua": "Bún riêu cua là món bún nước nấu từ gạch cua đồng với cà chua, vị chua dịu, ăn kèm rau sống.",
    "bun-dau-mam-tom": "Bún đậu mắm tôm gồm bún lá, đậu phụ rán vàng và các món ăn kèm, chấm mắm tôm vắt chanh đánh bông.",
    "kem": "Kem là món tráng miệng lạnh làm từ sữa và đường, có nhiều hương vị.",
    "che": "Chè là món tráng miệng ngọt nấu từ đậu, bột và nước cốt dừa, ăn nóng hoặc thêm đá.",
}

# Món mà bài Wikipedia cùng tên nói về NGUYÊN LIỆU hoặc CON VẬT, không phải MÓN ĂN.
# Đã kiểm bằng tay: bài "Ốc" nói về lớp Chân bụng (con ốc), không phải món ốc luộc.
# Với các món này chỉ dùng bản soạn tay, KHÔNG để Wikipedia ghi đè.
SKIP_WIKIPEDIA = {"oc-luoc", "com", "bun", "mien", "kem", "che", "xoi", "banh-mi"}


def main() -> int:
    if not SEED.exists():
        print(f"Khong tim thay {SEED}")
        return 1

    raw = json.loads(SEED.read_text(encoding="utf-8"))
    dishes = raw.get("dishes", [])

    removed_ingredients = 0
    filled_intro = 0
    marked_skip = 0

    for dish in dishes:
        dish_id = dish.get("dish_id")
        if "ingredients" in dish:
            dish.pop("ingredients")
            removed_ingredients += 1
        if dish_id in INTRO:
            dish["description"] = INTRO[dish_id]
            filled_intro += 1
        if dish_id in SKIP_WIKIPEDIA:
            dish["skip_wikipedia"] = True
            marked_skip += 1

    SEED.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"muc trong seed        : {len(dishes)}")
    print(f"da bo 'ingredients'   : {removed_ingredients}")
    print(f"da dien gioi thieu    : {filled_intro}")
    print(f"danh dau skip_wiki    : {marked_skip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
