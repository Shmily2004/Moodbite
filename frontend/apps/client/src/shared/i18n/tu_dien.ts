/**
 * TỪ ĐIỂN Việt–Anh. Nguồn sự thật duy nhất của mọi câu chữ trong giao diện.
 *
 * VÌ SAO TỰ VIẾT MÀ KHÔNG DÙNG `react-i18next`
 * --------------------------------------------
 * Thư viện đó mạnh ở những thứ dự án này KHÔNG cần: tải file dịch theo yêu cầu, dạng số
 * nhiều phức tạp, namespace lồng nhau, đổi ngôn ngữ ở server. Đổi lại nó thêm ~40KB và
 * một tầng cấu hình nữa. Ở đây chỉ có HAI ngôn ngữ và vài trăm câu, nên một object thuần
 * + một context là đủ, lại kiểm được kiểu lúc biên dịch (xem `Khoa` bên dưới).
 * Khi nào nên đổi ý: có ngôn ngữ thứ ba do người ngoài dịch, hoặc cần tách file dịch.
 *
 * ⚠️ GIỚI HẠN PHẢI NÓI RÕ — bật tiếng Anh KHÔNG dịch được những thứ sau:
 *   - Tên món, tên quán, địa chỉ            (dữ liệu thật, tiếng Việt)
 *   - Câu ngữ cảnh backend trả về           ("buổi tối", "trời mưa")
 *   - Thông báo lỗi từ API                  (backend sinh bằng tiếng Việt)
 *   - Giới thiệu món lấy từ Wikipedia tiếng Việt
 * Dịch được những thứ đó nghĩa là phải làm i18n Ở BACKEND — một việc riêng, tốn nhiều
 * hơn hẳn, và phải chốt trước. Giao diện đang nói thật điều này ở ô chọn ngôn ngữ.
 *
 * THÊM CHỮ MỚI: thêm một dòng vào `vi`, TypeScript sẽ bắt lỗi ở `en` cho tới khi bạn
 * dịch nốt. Không thể quên được — đó là lý do `en` khai kiểu `Record<Khoa, string>`.
 */

export const NGON_NGU = ['vi', 'en'] as const;
export type NgonNgu = (typeof NGON_NGU)[number];

/** Bản tiếng Việt là BẢN GỐC: nó định nghĩa danh sách khoá. */
const vi = {
  // --- Thanh trên -----------------------------------------------------------
  // --- Trang kết quả gợi ý món (thêm 2026-08-25) --------------------------
  'recommend.loading': 'Đang tìm món hợp với bạn…',
  'recommend.title': '{count} món phù hợp',
  'recommend.empty':
    'Không có món nào khớp bộ lọc hiện tại. Thử bỏ bớt một điều kiện hoặc nới bán kính nhé.',
  // --- Chân trang (thêm 2026-08-24) ---------------------------------------
  'footer.tagline': 'Gợi ý món ăn theo tâm trạng, thời tiết và giờ giấc của bạn.',
  'footer.scope': 'Phạm vi dữ liệu: Hà Nội.',
  'footer.navLabel': 'Liên kết trong trang',
  'footer.exploreTitle': 'Khám phá',
  'footer.account': 'Tài khoản của tôi',
  'footer.dataTitle': 'Nguồn dữ liệu',
  'footer.honestTitle': 'Nói rõ để bạn khỏi hiểu nhầm',
  'footer.dishDisclaimer':
    'Món ăn được SUY LUẬN từ tên quán, không phải đọc từ thực đơn thật — hãy gọi điện hỏi quán trước khi đi xa.',
  'footer.academic': 'MoodBite là đồ án tốt nghiệp, không phải dịch vụ thương mại.',
  'footer.copyright': '© 2026 MoodBite · Dữ liệu quán ăn thuộc về các nguồn mở nêu trên.',
  'nav.suggest': 'Gợi ý món ăn',
  'nav.search': 'Tìm bằng câu tự nhiên',
  'nav.account': 'Tài khoản của tôi',
  'nav.login': 'Đăng nhập',
  'nav.register': 'Đăng ký',
  'nav.logout': 'Đăng xuất',
  'nav.city': 'Hà Nội',
  'nav.cityHint': 'Dữ liệu MoodBite hiện chỉ có ở Hà Nội',
  'nav.home': 'MoodBite - trang chủ',
  'nav.main': 'Điều hướng chính',

  // --- Ngôn ngữ -------------------------------------------------------------
  'lang.label': 'Ngôn ngữ hiển thị',
  'lang.hint':
    'Giao diện dịch được. Tên món, tên quán và dữ liệu từ máy chủ vẫn là tiếng Việt.',

  // --- Khối mở đầu trang chủ ------------------------------------------------
  'hero.morning': 'Chào buổi sáng',
  'hero.noon': 'Chào buổi trưa',
  'hero.afternoon': 'Chào buổi chiều',
  'hero.evening': 'Chào buổi tối',
  'hero.titleLoggedIn': 'Hôm nay bạn muốn ăn gì?',
  'hero.introLoggedIn':
    'MoodBite đã tìm một số món có thể hợp với bạn, dựa trên thời điểm và thời tiết hiện tại.',
  'hero.introGuest':
    'MoodBite gợi ý những món ăn phù hợp với cảm xúc, thời tiết và thói quen của bạn.',
  'hero.searchLabel': 'Tìm món ăn hoặc quán ăn',
  'hero.searchPlaceholder': 'Tìm món ăn, quán ăn, món bạn muốn…',
  'hero.searchButton': 'Tìm ngay',
  'hero.nudge': 'để nhận gợi ý phù hợp với bạn hơn',
  'hero.signals': 'Ngữ cảnh đang được dùng để gợi ý',
  // Khẩu hiệu bản tiếng Việt là một BỨC ẢNH (bộ chữ riêng của thiết kế). Bản tiếng Anh
  // dựng bằng chữ vì không có ảnh tương ứng — xem `shared/ui/Slogan.tsx`.
  'hero.sloganLine1': 'Ăn gì ở Hà Nội,',
  'hero.sloganLine2a': 'tùy',
  'hero.sloganLine2b': 'của bạn.',

  // --- Chọn nhanh theo mood -------------------------------------------------
  'mood.titleGuest': 'Gợi ý nhanh theo mood',
  'mood.titleLoggedIn': 'Mood của bạn hôm nay là gì?',
  'mood.sub': 'Bấm một thẻ để lọc ngay. Bấm lại để bỏ chọn.',
  'mood.more': 'Xem thêm',

  'mood.card.excited': 'Thèm cay',
  'mood.card.relaxed': 'Thư giãn',
  'mood.card.happy': 'Vui vẻ',
  'mood.card.sad': 'Cần an ủi',
  'mood.card.rain': 'Trời mưa',
  'mood.card.nuong': 'Đồ nướng',
  'mood.card.hot': 'Món nóng',

  'need.gan-day.title': 'Ăn gần đây',
  'need.gan-day.desc': 'Món có quán trong bán kính 2 km',
  'need.an-dem.title': 'Ăn đêm',
  'need.an-dem.desc': 'Món hợp lúc đêm khuya',
  'need.bua-sang.title': 'Bữa sáng',
  'need.bua-sang.desc': 'Bắt đầu ngày mới nhẹ nhàng',
  'need.an-vat.title': 'Ăn vặt',
  'need.an-vat.desc': 'Món nhâm nhi giữa buổi',
  'need.mon-nuoc.title': 'Món nước',
  'need.mon-nuoc.desc': 'Phở, bún, miến… nóng hổi',
  'need.do-mat.title': 'Đồ mát',
  'need.do-mat.desc': 'Món nguội, giải nhiệt',

  // --- Khám phá theo nhu cầu ------------------------------------------------
  'needs.title': 'Khám phá theo nhu cầu',
  'needs.sub': 'Sáu lối vào nhanh, không cần tài khoản.',

  // --- Danh sách kết quả ----------------------------------------------------
  'results.titleGuest': 'Món phổ biến hôm nay',
  'results.titleLoggedIn': 'Gợi ý hôm nay dành cho {name}',
  'results.subGuest':
    'Món có nhiều quán ở Hà Nội đang bán, hợp với thời điểm và thời tiết lúc này.',
  'results.subLoggedIn': 'Dựa trên mood bạn chọn, thời tiết và thời điểm hiện tại.',
  'results.showAll': 'Xem tất cả ({count})',
  'results.collapse': 'Thu gọn',
  'results.emptyTitle': 'Không có món nào khớp',
  'results.emptyHint': 'Điều kiện đang hơi chặt. Thử bỏ bớt một vài bộ lọc.',
  'results.clearFilters': 'Xoá hết bộ lọc',
  'results.retry': 'Thử lại',

  'filters.title': 'Lọc chi tiết',
  'filters.sub': 'Mọi điều kiện mà bảy thẻ mood ở trên không phủ hết.',
  'filters.open': 'Lọc',
  'filters.close': 'Đóng bộ lọc',
  'filters.apply': 'Xem kết quả',

  // --- Mời đăng ký ----------------------------------------------------------
  'cta.title': 'Muốn MoodBite hiểu bạn hơn?',
  'cta.sub': 'Chọn mood và khẩu vị của bạn, MoodBite sẽ nhớ lại cho những lần sau.',
  'cta.explore': 'Khám phá ngay',
  'cta.register': 'Đăng ký tài khoản',

  // --- Trang tài khoản: khung -----------------------------------------------
  'account.sectionLabel': 'TÀI KHOẢN',
  'account.tab.overview': 'Tổng quan',
  'account.tab.profile': 'Hồ sơ cá nhân',
  'account.tab.taste': 'Sở thích & khẩu vị',
  'account.tab.saved': 'Quán & món đã lưu',
  'account.tab.recent': 'Đã xem gần đây',
  'account.tab.badges': 'Cấp độ & huy hiệu',
  'account.tab.settings': 'Cài đặt',

  // --- Trang tài khoản: nội dung --------------------------------------------
  'account.memberSince': 'Thành viên từ {date}',
  'account.noEmail': 'Chưa có email — bạn sẽ không tự lấy lại được mật khẩu nếu quên.',
  'account.stat.savedDishes': 'Món đã lưu',
  'account.stat.savedRestaurants': 'Quán yêu thích',
  'account.stat.viewed': 'Món đã xem',
  'account.stat.explorations': 'Lượt khám phá',
  'account.level.title': 'CẤP ĐỘ CỦA BẠN',
  'account.level.level': 'Cấp {n}',
  'account.level.points': '{points} / {next} điểm',
  'account.level.toNext': 'Khám phá thêm {n} điểm để lên cấp {level}',
  'account.level.max': 'Bạn đang ở cấp cao nhất.',
  'account.level.how': 'Điểm được tính thế nào?',
  'account.badges.title': 'HUY HIỆU CỦA BẠN',
  'account.badges.earned': 'Đã đạt',
  'account.badges.progress': '{current}/{target}',
  'account.saved.title': 'Quán & món đã lưu',
  'account.saved.empty': 'Chưa lưu gì. Bấm hình trái tim trên thẻ món để lưu lại.',
  'account.saved.count': '{n} mục',
  'account.saved.local':
    'Đang lưu trên máy này. Đăng nhập để đồng bộ giữa các thiết bị.',
  'account.saved.synced': 'Đã đồng bộ với tài khoản của bạn.',
  'account.recent.title': 'Đã xem gần đây',
  'account.recent.empty': 'Chưa mở món nào.',
  'account.recent.clear': 'Xoá lịch sử',
  'account.taste.title': 'Sở thích của bạn',
  'account.taste.sub': 'Chọn vài thứ bạn hay ăn. MoodBite sẽ bật sẵn các bộ lọc này.',
  'account.taste.clear': 'Xoá hết',
  'account.profile.title': 'Hồ sơ cá nhân',
  'account.profile.username': 'Tên đăng nhập',
  'account.profile.displayName': 'Tên hiển thị',
  'account.profile.email': 'Email',
  'account.profile.joined': 'Ngày tham gia',
  'account.profile.role': 'Vai',
  'account.profile.readonly':
    'Chưa sửa được ở đây: backend chưa có endpoint cập nhật hồ sơ. Xem PROJECT_CHECKLIST.md.',
  'account.settings.title': 'Cài đặt',
  'account.settings.dark': 'Giao diện nền tối',
  'account.settings.language': 'Ngôn ngữ',
  'account.settings.logout': 'Đăng xuất khỏi máy này',
  'account.settings.password': 'Đổi mật khẩu',
  'account.loginRequired': 'Bạn cần đăng nhập để xem trang này.',

  // --- Dùng chung -----------------------------------------------------------
  'common.viewAll': 'Xem tất cả',
  'common.loading': 'Đang tải…',
  'common.km': '{n} km',
} as const;

export type Khoa = keyof typeof vi;

/**
 * Bản tiếng Anh. Khai kiểu `Record<Khoa, string>` để thiếu MỘT câu là lỗi biên dịch —
 * không có cách nào quên dịch mà vẫn build được.
 */
const en: Record<Khoa, string> = {
  // --- Dish recommendation results page (added 2026-08-25) ----------------
  'recommend.loading': 'Finding dishes for you…',
  'recommend.title': '{count} matching dishes',
  'recommend.empty':
    'No dish matches the current filters. Try removing a condition or widening the radius.',
  // --- Footer (added 2026-08-24) ------------------------------------------
  'footer.tagline': 'Dish ideas that match your mood, the weather and the time of day.',
  'footer.scope': 'Data coverage: Hanoi only.',
  'footer.navLabel': 'Site links',
  'footer.exploreTitle': 'Explore',
  'footer.account': 'My account',
  'footer.dataTitle': 'Data sources',
  'footer.honestTitle': 'So there is no misunderstanding',
  'footer.dishDisclaimer':
    'Dishes are INFERRED from restaurant names, not read from real menus — call ahead before travelling far.',
  'footer.academic': 'MoodBite is a graduation project, not a commercial service.',
  'footer.copyright': '© 2026 MoodBite · Restaurant data belongs to the open sources listed above.',
  'nav.suggest': 'Dish ideas',
  'nav.search': 'Search in plain language',
  'nav.account': 'My account',
  'nav.login': 'Sign in',
  'nav.register': 'Sign up',
  'nav.logout': 'Sign out',
  'nav.city': 'Hanoi',
  'nav.cityHint': 'MoodBite data currently covers Hanoi only',
  'nav.home': 'MoodBite - home',
  'nav.main': 'Main navigation',

  'lang.label': 'Display language',
  'lang.hint':
    'The interface is translated. Dish names, restaurant names and server data stay in Vietnamese.',

  'hero.morning': 'Good morning',
  'hero.noon': 'Good afternoon',
  'hero.afternoon': 'Good afternoon',
  'hero.evening': 'Good evening',
  'hero.titleLoggedIn': 'What do you feel like eating today?',
  'hero.introLoggedIn':
    'MoodBite picked a few dishes that may suit you, based on the time of day and the weather.',
  'hero.introGuest':
    'MoodBite suggests dishes that match your mood, the weather and your habits.',
  'hero.searchLabel': 'Search for a dish or a restaurant',
  'hero.searchPlaceholder': 'Search a dish, a place, anything you crave…',
  'hero.searchButton': 'Search',
  'hero.nudge': 'to get suggestions that fit you better',
  'hero.signals': 'Context used for these suggestions',
  'hero.sloganLine1': 'What to eat in Hanoi,',
  'hero.sloganLine2a': 'follow your',
  'hero.sloganLine2b': 'today.',

  'mood.titleGuest': 'Quick picks by mood',
  'mood.titleLoggedIn': "What's your mood today?",
  'mood.sub': 'Tap a card to filter. Tap again to clear.',
  'mood.more': 'More',

  'mood.card.excited': 'Craving spice',
  'mood.card.relaxed': 'Unwind',
  'mood.card.happy': 'Cheerful',
  'mood.card.sad': 'Comfort food',
  'mood.card.rain': 'Rainy day',
  'mood.card.nuong': 'Grilled',
  'mood.card.hot': 'Hot dishes',

  'need.gan-day.title': 'Eat nearby',
  'need.gan-day.desc': 'Dishes served within 2 km',
  'need.an-dem.title': 'Late night',
  'need.an-dem.desc': 'Dishes that suit the small hours',
  'need.bua-sang.title': 'Breakfast',
  'need.bua-sang.desc': 'A gentle start to the day',
  'need.an-vat.title': 'Snacks',
  'need.an-vat.desc': 'Something to nibble between meals',
  'need.mon-nuoc.title': 'Noodle soups',
  'need.mon-nuoc.desc': 'Pho, bun, mien… piping hot',
  'need.do-mat.title': 'Cool dishes',
  'need.do-mat.desc': 'Served cold, refreshing',

  'needs.title': 'Explore by need',
  'needs.sub': 'Six quick entry points, no account needed.',

  'results.titleGuest': 'Popular dishes today',
  'results.titleLoggedIn': "Today's picks for {name}",
  'results.subGuest':
    'Dishes served by many places in Hanoi, matching the current time and weather.',
  'results.subLoggedIn': 'Based on the mood you picked, the weather and the time of day.',
  'results.showAll': 'View all ({count})',
  'results.collapse': 'Collapse',
  'results.emptyTitle': 'No dish matches',
  'results.emptyHint': 'Your filters are a bit tight. Try removing one or two.',
  'results.clearFilters': 'Clear all filters',
  'results.retry': 'Try again',

  'filters.title': 'Detailed filters',
  'filters.sub': "Everything the seven mood cards above don't cover.",
  'filters.open': 'Filters',
  'filters.close': 'Close filters',
  'filters.apply': 'Show results',

  'cta.title': 'Want MoodBite to know you better?',
  'cta.sub': 'Pick your mood and taste, and MoodBite will remember them next time.',
  'cta.explore': 'Start exploring',
  'cta.register': 'Create an account',

  'account.sectionLabel': 'ACCOUNT',
  'account.tab.overview': 'Overview',
  'account.tab.profile': 'Profile',
  'account.tab.taste': 'Taste & preferences',
  'account.tab.saved': 'Saved places & dishes',
  'account.tab.recent': 'Recently viewed',
  'account.tab.badges': 'Level & badges',
  'account.tab.settings': 'Settings',

  'account.memberSince': 'Member since {date}',
  'account.noEmail': "No email yet — you won't be able to reset your password.",
  'account.stat.savedDishes': 'Saved dishes',
  'account.stat.savedRestaurants': 'Favourite places',
  'account.stat.viewed': 'Dishes viewed',
  'account.stat.explorations': 'Explorations',
  'account.level.title': 'YOUR LEVEL',
  'account.level.level': 'Level {n}',
  'account.level.points': '{points} / {next} points',
  'account.level.toNext': 'Earn {n} more points to reach level {level}',
  'account.level.max': "You're at the highest level.",
  'account.level.how': 'How are points counted?',
  'account.badges.title': 'YOUR BADGES',
  'account.badges.earned': 'Earned',
  'account.badges.progress': '{current}/{target}',
  'account.saved.title': 'Saved places & dishes',
  'account.saved.empty': 'Nothing saved yet. Tap the heart on a dish card to save it.',
  'account.saved.count': '{n} items',
  'account.saved.local': 'Stored on this device. Sign in to sync across devices.',
  'account.saved.synced': 'Synced with your account.',
  'account.recent.title': 'Recently viewed',
  'account.recent.empty': "You haven't opened any dish yet.",
  'account.recent.clear': 'Clear history',
  'account.taste.title': 'Your taste',
  'account.taste.sub':
    'Pick a few things you eat often. MoodBite will pre-apply those filters.',
  'account.taste.clear': 'Clear all',
  'account.profile.title': 'Profile',
  'account.profile.username': 'Username',
  'account.profile.displayName': 'Display name',
  'account.profile.email': 'Email',
  'account.profile.joined': 'Joined',
  'account.profile.role': 'Role',
  'account.profile.readonly':
    'Not editable yet: the backend has no profile-update endpoint. See PROJECT_CHECKLIST.md.',
  'account.settings.title': 'Settings',
  'account.settings.dark': 'Dark theme',
  'account.settings.language': 'Language',
  'account.settings.logout': 'Sign out of this device',
  'account.settings.password': 'Change password',
  'account.loginRequired': 'You need to sign in to view this page.',

  'common.viewAll': 'View all',
  'common.loading': 'Loading…',
  'common.km': '{n} km',
};

export const TU_DIEN: Record<NgonNgu, Record<Khoa, string>> = { vi, en };

/**
 * Thay `{ten}` bằng giá trị thật.
 *
 * Cố ý RẤT ĐƠN GIẢN: không có định dạng số, không có dạng số nhiều. Chưa câu nào cần tới,
 * và thêm sớm chỉ tạo ra một hệ thống nhỏ nữa để bảo trì.
 */
export function thay_the(mau: string, gia_tri?: Record<string, string | number>): string {
  if (!gia_tri) return mau;
  return mau.replace(/\{(\w+)\}/g, (nguyen_ban, ten) =>
    ten in gia_tri ? String(gia_tri[ten]) : nguyen_ban,
  );
}
