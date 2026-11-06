# -*- coding: utf-8 -*-
"""Tính năng chính + điểm mạnh nổi bật (tiếng Việt) cho các repo đáng chú ý.
f = tính năng chính, s = điểm mạnh nổi bật khi đóng gói bán cho SME Việt Nam.
Tổng hợp từ README của repo; nên mở bản demo để xác nhận trước khi chào khách.
"""

CURATED = {
# ---------- Chat & chăm sóc khách hàng ----------
"chatwoot/chatwoot": dict(
    f=["Hộp thư chung gom live chat web, email, Facebook, Instagram, WhatsApp, Telegram, SMS", "Ghi chú nội bộ, @nhắc đồng nghiệp, gắn nhãn, phân công hội thoại", "Quản lý liên hệ, phân nhóm khách, chiến dịch nhắn chủ động", "Mẫu trả lời nhanh, phím tắt, thanh lệnh", "Trợ lý AI, tích hợp chatbot (Dialogflow), Slack, ứng dụng nhúng", "Báo cáo thời gian phản hồi, CSAT, hiệu suất từng nhân viên"],
    s=["Gần như là 'Intercom mã nguồn mở' — giao diện hoàn thiện, khách dễ dùng ngay", "Kiến trúc kênh (inbox) rõ ràng: thêm Zalo OA như một kênh mới là hướng cải tiến tự nhiên", "Cộng đồng lớn, cập nhật đều; phần lõi MIT cho phép host nhiều khách"]),
"useopendesk/opendesk": dict(
    f=["Hộp thư ticket: trạng thái, ưu tiên, người phụ trách, nhóm, tag, SLA", "Nhận email hỗ trợ và trả lời qua Google/Microsoft/SMTP", "Widget live chat nhúng website có xác thực danh tính", "Trung tâm trợ giúp công khai (knowledge base)", "Bot AI soạn nháp, tóm tắt, phân loại, dịch, trả lời từ kho kiến thức", "Tự động hóa, SLA, báo cáo CSAT; REST API, webhook"],
    s=["Gói đủ bộ helpdesk hiện đại (ticket + chat + help center + AI) trong một sản phẩm", "Apache-2.0: thoải mái làm SaaS nhiều khách", "Repo còn mới, ít sao — cần thử kỹ độ ổn định trước khi bán"]),
"abhinavxd/libredesk": dict(
    f=["Hộp thư chung: email, live chat, WhatsApp", "Widget chat thời gian thực cho website", "Trung tâm trợ giúp đa ngôn ngữ", "Trợ lý AI trả lời từ kho kiến thức, chuyển cho người thật", "Macro, quy tắc tự động gắn tag/phân công, chia việc theo năng lực"],
    s=["Chạy bằng một file duy nhất — cực nhẹ, chi phí server thấp, hợp gói giá rẻ", "Dễ cài cho từng khách riêng, ít việc vận hành"]),
"django-crm/django-crm": dict(
    f=["CRM bán hàng: lead, cơ hội, khách hàng, liên hệ", "Helpdesk có SLA, phê duyệt, leo thang, macro", "Hóa đơn ngay trong cùng ứng dụng", "Ứng dụng web + mobile + REST API", "Multi-tenant sẵn bằng Row-Level Security của PostgreSQL"],
    s=["MIT, không giới hạn user — khớp chiến lược bán giá trọn gói không tính theo đầu người", "Thiết kế multi-tenant sẵn: một server phục vụ nhiều khách, chi phí vận hành thấp", "Stack Django + Svelte phổ biến, dễ thuê dev VN sửa"]),
"zammad/zammad": dict(
    f=["Ticket đa kênh: email, chat, điện thoại, Facebook, Telegram, WhatsApp", "Knowledge base, mẫu trả lời, SLA, trình kích hoạt tự động", "Phân quyền chi tiết, nhóm, tổ chức khách hàng", "Tích hợp tổng đài, LDAP, báo cáo"],
    s=["Helpdesk lâu năm, ổn định, được doanh nghiệp châu Âu dùng nhiều", "Hợp khách có đội CSKH 10+ người cần quy trình chặt"]),
"frappe/helpdesk": dict(
    f=["Ticket với SLA, phân công, mẫu trả lời", "Cổng tự phục vụ cho khách, knowledge base", "Giao diện agent hiện đại", "Nối thẳng với ERPNext/Frappe CRM"],
    s=["Cùng hệ sinh thái Frappe: bán combo CRM + Helpdesk + ERP cho một khách", "Cộng đồng Frappe có đối tác tại châu Á"]),
"glpi-project/glpi": dict(
    f=["Service desk chuẩn ITIL: yêu cầu, sự cố, vấn đề, thay đổi", "Quản lý tài sản IT, license phần mềm, hợp đồng", "Danh mục dịch vụ có SLA", "Quản lý trung tâm dữ liệu, đặt mượn thiết bị"],
    s=["Chuẩn cho phòng IT nội bộ — bán cho trường học, nhà máy, chuỗi văn phòng", "Rất trưởng thành (20+ năm), nhiều plugin"]),

# ---------- CRM ----------
"krayin/laravel-crm": dict(
    f=["Quản lý lead, khách hàng, liên hệ, tổ chức", "Pipeline bán hàng kéo thả, nhiều giai đoạn", "Báo giá, sản phẩm, hoạt động (gọi, họp, email)", "Thuộc tính tùy biến, phân quyền vai trò", "Nhận lead từ email và form web"],
    s=["Laravel/PHP — thuê dev VN dễ, hosting rẻ", "MIT, giao diện quen thuộc kiểu Pipedrive, dễ Việt hóa", "Cùng nhà phát triển với Bagisto: có thể ghép CRM + web bán hàng"]),
"twentyhq/twenty": dict(
    f=["CRM hiện đại kiểu Notion/Airtable: tự tạo đối tượng, trường dữ liệu", "Pipeline, công việc, ghi chú, dòng thời gian", "Đồng bộ email và lịch", "Workflow tự động, API/GraphQL, webhook", "Nhiều chế độ xem: bảng, kanban"],
    s=["Giao diện đẹp nhất trong nhóm CRM mã nguồn mở, cộng đồng rất lớn", "Tùy biến sâu theo ngành mà không cần sửa code lõi", "AGPL + phần enterprise riêng: chỉ dùng lõi, công khai phần sửa"]),
"frappe/crm": dict(
    f=["Lead, deal, pipeline kanban", "Gọi điện, email, WhatsApp ngay trong CRM", "Ghi chú, công việc, SLA phản hồi lead", "Liên kết ERPNext để chuyển deal thành đơn hàng"],
    s=["Gọn, hiện đại, cùng hệ Frappe — ghép được với ERP/HR/Helpdesk", "Hợp mô hình bán dự án trọn bộ cho SME"]),
"espocrm/espocrm": dict(
    f=["Lead, cơ hội, tài khoản, liên hệ, chiến dịch", "Quy trình công việc, phê duyệt, báo cáo", "Trình tùy biến thực thể và bố cục không cần code", "Email, lịch, cổng khách hàng, REST API"],
    s=["Rất trưởng thành, nhẹ, chạy tốt trên hosting PHP giá rẻ", "Tùy biến kéo thả mạnh — làm CRM theo ngành nhanh"]),
"sneg55/warpdrive": dict(
    f=["Bảng kanban kéo thả, nhiều pipeline, giai đoạn tùy biến", "Tổng giá trị có trọng số, cảnh báo deal 'nguội'", "Không gian deal: hoạt động, ghi chú, file, email theo dòng thời gian", "Người & tổ chức với trường tùy biến, nhập CSV có hoàn tác"],
    s=["Bản thay thế Pipedrive tập trung đúng việc bán hàng B2B", "Repo mới, ít sao — hợp để học và thử, rủi ro duy trì cao hơn"]),
"arnasdon/wacrm": dict(
    f=["Hộp thư chung cho WhatsApp", "Danh bạ, pipeline bán hàng", "Gửi tin hàng loạt (broadcast)", "Tự động hóa không cần code"],
    s=["Thiết kế sẵn để 'fork, gắn thương hiệu, host' — đúng mô hình bán lại", "Ý tưởng chuyển thẳng sang Zalo OA cho thị trường VN"]),
"melgarafael/deskcommcrm": dict(
    f=["CRM bán hàng tích hợp WhatsApp (WAHA)", "Agent AI trả lời và chăm sóc khách", "Tự động hóa theo quy tắc KHI/NẾU/THÌ", "Cài đặt tự động: HTTPS, admin, cơ sở dữ liệu"],
    s=["Gộp CRM + inbox + AI trong một — giống mô hình bạn định bán", "Tài liệu tiếng Bồ Đào Nha; cần Việt hóa và thay WhatsApp bằng Zalo"]),
"monicahq/monica": dict(
    f=["Quản lý liên hệ và mối quan hệ", "Nhắc sinh nhật, nhắc liên lạc", "Ghi chú, hoạt động, công việc theo từng người"],
    s=["CRM cá nhân — hợp người làm môi giới, bảo hiểm cá nhân hơn là doanh nghiệp"]),

# ---------- ERP / kế toán / hóa đơn ----------
"frappe/erpnext": dict(
    f=["Kế toán, công nợ, dòng tiền", "Bán hàng, mua hàng, kho, đơn hàng", "Sản xuất: định mức nguyên liệu (BOM), lệnh sản xuất", "Quản lý tài sản, dự án, nhân sự (qua Frappe HR)", "Phân quyền, quy trình phê duyệt, báo cáo tùy biến"],
    s=["ERP mã nguồn mở đầy đủ nhất cho SME, cộng đồng toàn cầu lớn", "Hợp ngách 'ERP sản xuất cho xưởng 20–100 người'", "GPL: host được; cài cho khách thì giao kèm mã nguồn"]),
"odoo/odoo": dict(
    f=["Hàng chục ứng dụng: CRM, bán hàng, kho, mua hàng, sản xuất, website, POS, kế toán", "Kiến trúc module: cài app nào dùng app đó", "Kho module cộng đồng rất lớn"],
    s=["Bản Community LGPL dùng thương mại được; bản Enterprise là trả phí riêng", "Đã có nhiều đối tác Odoo tại VN — cạnh tranh, cần ngách rõ"]),
"aureuserp/aureuserp": dict(
    f=["ERP module hóa trên Laravel + Filament", "Các module kinh doanh cơ bản: bán hàng, mua hàng, kho, nhân sự, dự án"],
    s=["MIT, stack Laravel hiện đại, dễ tùy biến", "Còn non trẻ so với ERPNext/Odoo — hợp làm nền cho sản phẩm ngách riêng"]),
"invoiceplane/invoiceplane": dict(
    f=["Tạo, gửi, quản lý hóa đơn và báo giá", "Quản lý khách hàng, sản phẩm, công việc", "Theo dõi thanh toán, nhắc nợ, nhiều cổng thanh toán", "Mẫu hóa đơn tùy biến, báo cáo tài chính"],
    s=["Gọn, đúng việc cho freelancer/agency nhỏ", "Lưu ý: hóa đơn này không thay hóa đơn điện tử theo luật VN — chỉ là báo giá/đề nghị thanh toán"]),
"solidinvoice/solidinvoice": dict(
    f=["Báo giá chuyển thành hóa đơn một chạm", "Hóa đơn định kỳ", "Đa tiền tệ", "Quản lý khách hàng, liên hệ, trường tùy biến", "Bảo mật 2 lớp, đăng nhập Google"],
    s=["Hóa đơn định kỳ hợp mô hình thu phí thuê bao (trung tâm, dịch vụ)"]),
"vas3k/taxhacker": dict(
    f=["Tải lên hóa đơn, biên lai, sao kê", "AI tự trích ngày, số tiền, người bán", "Tự phân loại giao dịch, đa tiền tệ theo tỷ giá ngày giao dịch", "Dùng mô hình AI của bạn (cả chạy nội bộ)"],
    s=["AI đọc chứng từ — ý tưởng hay cho dịch vụ kế toán thuê ngoài VN", "Cần dạy lại cho mẫu hóa đơn VAT Việt Nam"]),
"ever-co/ever-gauzy": dict(
    f=["ERP + CRM + nhân sự + tuyển dụng + quản lý dự án", "Chấm công, theo dõi thời gian và năng suất", "Quản lý bán hàng, hóa đơn, chi phí"],
    s=["Rất nhiều module trong một — hợp agency/công ty dịch vụ tính phí theo giờ"]),
"kimai/kimai": dict(
    f=["Ghi giờ làm theo dự án, khách hàng, hoạt động", "Bảng chấm công, xuất hóa đơn theo giờ", "Ngân sách dự án, báo cáo", "Đa người dùng, phân quyền, plugin"],
    s=["Hợp agency, studio, công ty outsource tính tiền theo giờ", "Trưởng thành, ổn định, nhiều ngôn ngữ"]),

# ---------- Nhân sự ----------
"frappe/hrms": dict(
    f=["Hồ sơ nhân viên, tuyển dụng, onboarding", "Chấm công, nghỉ phép, ca làm", "Tính lương, phúc lợi, tạm ứng, chi phí", "Đánh giá hiệu suất, app mobile"],
    s=["HR + lương đầy đủ, nối ERPNext", "Cần làm thêm quy tắc BHXH, thuế TNCN Việt Nam"]),

# ---------- TMĐT ----------
"bagisto/bagisto": dict(
    f=["Web bán hàng + chợ nhiều người bán", "Đa kênh, đa kho, đa tiền tệ, đa ngôn ngữ", "Quản lý sản phẩm lớn (công bố 10 triệu+ SKU)", "Có bản B2B, POS, mobile app"],
    s=["Laravel — dev VN quen, hosting rẻ", "Có sẵn hướng B2B: hợp ngách 'cổng đặt hàng cho đại lý'"]),
"saleor/saleor": dict(
    f=["API thương mại headless (GraphQL)", "Đa kênh, đa kho, khuyến mãi, quà tặng", "Hệ app mở rộng tách rời lõi", "Dashboard quản trị"],
    s=["Hiệu năng cao, kiến trúc hiện đại cho thương hiệu lớn", "Cần đội frontend riêng — nặng cho shop nhỏ"]),
"shopware/shopware": dict(
    f=["Nền tảng thương mại đầy đủ: giỏ hàng, quản trị, API-first", "Hơn 3.000 tiện ích cộng đồng", "Rule builder khuyến mãi, quy trình"],
    s=["Mạnh ở châu Âu; cộng đồng VN ít — cân nhắc chi phí học"]),
"aimeos/aimeos": dict(
    f=["Shop Laravel cực nhanh, từ 1 đến hàng tỷ sản phẩm", "Đa nhà bán, đa kênh, đa kho", "Gói, voucher, sản phẩm số, thuê bao định kỳ", "Thiết kế cho SaaS TMĐT multi-tenant"],
    s=["Hỗ trợ multi-tenant sẵn — hợp làm nền tảng shop cho nhiều khách", "B2B phức tạp được"]),
"vendurehq/vendure": dict(
    f=["Thương mại headless trên Node.js/TypeScript", "Plugin, đa kênh, khuyến mãi linh hoạt", "API GraphQL, dashboard quản trị"],
    s=["Dev JS/TS dễ mở rộng", "Hợp đội có năng lực kỹ thuật, khách thương hiệu"]),
"nopsolutions/nopcommerce": dict(
    f=["Shop đầy đủ trên ASP.NET Core", "Đa cửa hàng, đa nhà bán", "Hàng nghìn plugin, theme"],
    s=["Hợp khách/đội đã dùng hệ sinh thái Microsoft"]),
"woocommerce/woocommerce": dict(
    f=["Plugin bán hàng cho WordPress", "Kho tiện ích khổng lồ, nhiều plugin thanh toán/vận chuyển VN đã có"],
    s=["Phổ biến nhất VN — dễ bán, nhưng cạnh tranh cực cao; chỉ bán kèm dịch vụ vận hành"]),

# ---------- Bán hàng & kho ----------
"opensourcepos/opensourcepos": dict(
    f=["Bán hàng tại quầy, in hóa đơn, mã vạch", "Quản lý kho, nhà cung cấp, nhập hàng", "Khách hàng, giảm giá, quà tặng", "Báo cáo bán hàng, nhiều ngôn ngữ"],
    s=["Web POS nhẹ, chạy PHP — hợp cửa hàng nhỏ", "Cạnh tranh trực tiếp KiotViet/Sapo — chỉ đánh ngách kho"]),
"greaterwms/greaterwms": dict(
    f=["Quản lý kho: nhập, xuất, tồn, vị trí", "Quy trình kho theo chuẩn chuỗi cung ứng hậu mãi", "App quét mã trên điện thoại"],
    s=["Xuất phát từ quy trình kho thực tế của doanh nghiệp lớn", "Hợp ngách 'kho cho phụ tùng/vật tư'"]),

# ---------- F&B / khách sạn ----------
"tastyigniter/tastyigniter": dict(
    f=["Web đặt món trực tuyến cho nhà hàng", "Đặt bàn, quản lý thực đơn, nhiều chi nhánh", "Giao hàng/lấy tại quán, khuyến mãi"],
    s=["Đúng ngách 'kênh đặt món riêng, tránh phí app giao đồ ăn'", "MIT, Laravel — thêm VietQR dễ"]),
"qloapps/qloapps": dict(
    f=["Đặt phòng khách sạn trực tuyến + quản lý khách sạn", "Quản lý phòng, giá theo mùa, tiện nghi", "Đồng bộ OTA qua channel manager (tiện ích)"],
    s=["Hợp homestay, khách sạn mini muốn web đặt phòng riêng", "OSL-3.0 (giống AGPL): phải công khai phần sửa"]),

# ---------- Phân tích ----------
"apache/superset": dict(
    f=["Tạo biểu đồ không cần code", "Trình soạn SQL trên web", "Lớp ngữ nghĩa định nghĩa chỉ số", "Kết nối gần như mọi CSDL", "Phân quyền, cache, API"],
    s=["Công cụ BI mạnh, miễn phí — dùng làm lớp hiển thị cho dịch vụ báo cáo đa kênh"]),
"getredash/redash": dict(
    f=["Kết nối nhiều nguồn dữ liệu, viết truy vấn", "Dựng dashboard, chia sẻ", "Cảnh báo khi số liệu vượt ngưỡng"],
    s=["Nhẹ, dễ cài hơn Superset; hợp dashboard nhỏ cho chủ shop"]),
"umami-software/umami": dict(
    f=["Thống kê website: lượt xem, nguồn, thiết bị", "Không cookie — tôn trọng quyền riêng tư", "Theo dõi sự kiện, chuyển đổi, chiến dịch, doanh thu", "Nhiều website trong một tài khoản"],
    s=["Gọn, đẹp, nhẹ; bán kèm gói web cho agency", "Không dùng cookie: điểm cộng với luật bảo vệ dữ liệu mới"]),
"plausible/analytics": dict(
    f=["Phân tích website gọn nhẹ, không cookie", "Mục tiêu, chuyển đổi, nguồn truy cập", "Báo cáo email định kỳ"],
    s=["Thay Google Analytics cho khách quan tâm quyền riêng tư"]),
"metabase/metabase": dict(
    f=["Đặt câu hỏi dữ liệu không cần SQL", "Dashboard, cảnh báo, báo cáo định kỳ", "Nhúng biểu đồ vào ứng dụng khác"],
    s=["Dễ dùng nhất cho người không kỹ thuật", "AGPL + bản thương mại riêng cho tính năng nhúng nâng cao"]),
"posthog/posthog": dict(
    f=["Phân tích sản phẩm, phễu, giữ chân người dùng", "Ghi lại phiên (session replay)", "Feature flag, A/B test, khảo sát"],
    s=["Bộ công cụ cho startup làm app; phần 'ee' là thương mại riêng"]),
"msgbyte/tianji": dict(
    f=["Thống kê website + giám sát uptime + trạng thái server", "Thông báo sự cố, trang trạng thái", "Làm việc nhóm, OpenAPI"],
    s=["Gộp 3 công cụ vào một — bán kèm gói bảo trì web cho agency"]),

# ---------- Marketing ----------
"knadh/listmonk": dict(
    f=["Quản lý danh sách email, chiến dịch newsletter", "Mẫu email, phân nhóm theo truy vấn", "Gửi tốc độ cao, thống kê mở/nhấp", "Một file chạy duy nhất"],
    s=["Cực nhẹ, rẻ để vận hành", "Ở VN email kém hiệu quả — nên ghép thêm kênh Zalo ZNS"]),
"mautic/mautic": dict(
    f=["Marketing tự động: luồng chăm sóc nhiều bước", "Chấm điểm lead, phân nhóm", "Email, landing page, form", "Theo dõi hành vi trên website"],
    s=["Marketing automation mã nguồn mở đầy đủ nhất", "Hợp mô hình white-label cho agency"]),
"coollabsio/shoutrrr": dict(
    f=["Soạn một lần, đăng lên nhiều mạng xã hội", "Hàng đợi bài, khung giờ định kỳ, lịch tháng", "Workspace cho nhóm, phân vai trò", "Thống kê follower và tương tác từng bài"],
    s=["Thay Buffer/Hootsuite — bán cho agency quản lý nhiều page", "Apache-2.0, chạy Docker"]),
"brightbeanxyz/brightbean-studio": dict(
    f=["Lên lịch, đăng và quản lý nội dung trên 10+ nền tảng", "Một dashboard cho Facebook, Instagram, Threads...", "Quản lý tương tác, tin nhắn page"],
    s=["Có cả đăng bài và inbox page — hợp agency chăm fanpage cho SME"]),

# ---------- Tự động hóa / AI ----------
"activepieces/activepieces": dict(
    f=["Trình dựng luồng tự động kéo thả (thay Zapier)", "Hàng trăm 'piece' kết nối ứng dụng", "Viết piece mới bằng TypeScript", "Bước AI, nhánh, vòng lặp, phê duyệt của người"],
    s=["Lõi MIT (khác n8n bị hạn chế) — bán dịch vụ tự động hóa được", "Viết piece cho Zalo, payOS, GHN... thành tài sản riêng của bạn"]),
"langgenius/dify": dict(
    f=["Dựng ứng dụng AI, chatbot, agent bằng giao diện kéo thả", "RAG: nạp tài liệu làm kho kiến thức", "Hỗ trợ nhiều mô hình AI", "API để nhúng vào sản phẩm khác"],
    s=["Mạnh và phổ biến nhất nhóm nền tảng AI", "Bắt buộc triển khai riêng từng khách, giữ logo — không gom multi-tenant"]),
"open-webui/open-webui": dict(
    f=["Giao diện chat AI tự host (kiểu ChatGPT)", "Dùng nhiều mô hình, cả chạy nội bộ", "RAG với tài liệu, phân quyền người dùng"],
    s=["Bán 'ChatGPT nội bộ' cho doanh nghiệp lo lộ dữ liệu", "Có điều khoản giữ thương hiệu Open WebUI — đọc kỹ license"]),
"mintplex-labs/anything-llm": dict(
    f=["Chat với tài liệu (RAG) trong một ứng dụng", "Chạy mô hình nội bộ hoặc qua API", "Dựng agent không cần code, tác vụ định kỳ", "Đa người dùng, workspace riêng"],
    s=["MIT, cài dễ — hợp gói 'trợ lý tra cứu tài liệu nội bộ'"]),
"1panel-dev/maxkb": dict(
    f=["Nền tảng agent/kho kiến thức cho doanh nghiệp", "RAG, workflow, nhúng chatbot vào web", "Hỗ trợ nhiều mô hình AI"],
    s=["Thiết kế cho chatbot CSKH trên kho kiến thức — đúng ngách chatbot cho shop/phòng khám", "Giao diện ưu tiên tiếng Trung — cần Việt hóa"]),
"tencent/weknora": dict(
    f=["Biến tài liệu thô thành kho hỏi đáp RAG", "Agent suy luận, wiki tự cập nhật", "Hỏi đáp qua nhiều app chat", "Thay được mô hình, CSDL vector"],
    s=["Từ Tencent, cập nhật nhanh; hợp trợ lý tài liệu nội bộ"]),
"infiniflow/ragflow": dict(
    f=["RAG hiểu tài liệu sâu: bảng, PDF scan, bố cục", "Trích dẫn nguồn câu trả lời", "Agent, workflow"],
    s=["Mạnh nhất khi tài liệu phức tạp (hợp đồng, quy trình, hồ sơ)"]),
"dograh-hq/dograh": dict(
    f=["Nền tảng voice AI tự host (thay Vapi, Retell)", "Dựng kịch bản cuộc gọi bằng workflow trực quan", "Nối tổng đài Twilio, Vonage..., chuyển máy cho người thật", "Tự chọn mô hình giọng nói và AI"],
    s=["Ý tưởng lớn cho VN: tổng đài AI gọi nhắc lịch, xác nhận đơn", "Cần mô hình giọng tiếng Việt và nhà mạng VN (Stringee...)"]),
"iflytek/astron-rpa": dict(
    f=["RPA: tự động thao tác phần mềm, web như người", "Công cụ tự động hóa dựng sẵn, sẵn sàng cho agent AI"],
    s=["Tự động nhập liệu vào phần mềm cũ không có API (kế toán, cổng thuế)"]),

# ---------- Quản lý công việc ----------
"usekaneo/kaneo": dict(
    f=["Bảng, danh sách, lịch, Gantt, backlog", "Mô tả, đính kèm, việc con, phụ thuộc", "Workspace nhóm, vai trò, cập nhật thời gian thực", "Thông báo, webhook, REST API, tích hợp GitHub"],
    s=["Gọn, đẹp, MIT — làm nền cho ngách 'quản lý công trình'"]),
"wekan/wekan": dict(
    f=["Bảng kanban kiểu Trello", "Dịch sẵn 234 ngôn ngữ", "Nhiều lựa chọn CSDL"],
    s=["Đã có tiếng Việt, rất lâu năm", "Bản chung, khó bán nếu không làm theo ngành"]),
"makeplane/plane": dict(
    f=["Quản lý dự án kiểu Jira/Linear: issue, chu kỳ, module", "Trang tài liệu, phân tích tiến độ"],
    s=["Phổ biến, giao diện hiện đại; AGPL + bản thương mại"]),
"kanboard/kanboard": dict(
    f=["Kanban tối giản, nhiều plugin"],
    s=["Siêu nhẹ, ổn định lâu năm"]),

# ---------- Ký tài liệu / form ----------
"documenso/documenso": dict(
    f=["Ký tài liệu điện tử (thay DocuSign)", "Gửi cho nhiều người ký, theo thứ tự", "Mẫu tài liệu, lưu vết, API"],
    s=["Phù hợp ký nội bộ; văn bản cần giá trị pháp lý VN phải tích hợp chữ ký số CA", "Có phần ee thương mại riêng"]),
"opensignlabs/opensign": dict(
    f=["Ký PDF điện tử, nhiều người ký", "Mẫu, nhắc ký, lưu vết kiểm toán"],
    s=["Thay DocuSign miễn phí, hợp ký biên bản nội bộ"]),
"didi/xiaoju-survey": dict(
    f=["Nhiều loại câu hỏi: nhập liệu, chọn, chấm điểm, bình chọn, tải file", "Logic hiển thị/nhảy câu", "Phân quyền nhóm, phân tích chéo, xuất dữ liệu", "AI tạo bảng hỏi, tùy biến thương hiệu"],
    s=["Từ DiDi, khả năng phân tích mạnh — hợp khảo sát hài lòng chuỗi phòng khám/nhà hàng"]),
"heyform/heyform": dict(
    f=["Form hội thoại kiểu Typeform", "Logic, biến, tích hợp"],
    s=["Form đẹp, tăng tỉ lệ điền; chỉ bán được khi gắn thanh toán/check-in"]),
"formbricks/formbricks": dict(
    f=["Khảo sát trong ứng dụng, web, link", "Nhắm đối tượng, phân tích phản hồi"],
    s=["Hợp khảo sát trải nghiệm khách; có phần enterprise riêng"]),

# ---------- Website / CMS ----------
"payloadcms/payload": dict(
    f=["CMS headless + khung ứng dụng trên Next.js", "Tự định nghĩa nội dung bằng code, phân quyền", "Quản trị tự sinh, API REST/GraphQL"],
    s=["MIT, hợp agency dựng web hàng loạt trên một nền tảng"]),
"strapi/strapi": dict(
    f=["CMS headless, dựng kiểu nội dung bằng giao diện", "API REST/GraphQL, plugin, đa ngôn ngữ"],
    s=["Phổ biến với dev JS; có phần enterprise riêng"]),
"directus/directus": dict(
    f=["Biến CSDL SQL bất kỳ thành API + giao diện quản trị", "Phân quyền, luồng tự động, dashboard"],
    s=["Làm 'admin panel' nhanh cho dữ liệu sẵn có của khách"]),

# ---------- Đào tạo ----------
"frappe/lms": dict(
    f=["Khóa học, bài học, quiz, chứng chỉ", "Lớp học theo đợt, lịch học", "Bán khóa học, cổng thanh toán"],
    s=["Gọn, hiện đại; thêm VietQR là bán được cho trung tâm"]),
"chamilo/chamilo-lms": dict(
    f=["LMS đầy đủ: khóa học, bài kiểm tra, diễn đàn, chứng chỉ", "Theo dõi tiến độ học viên"],
    s=["Lâu năm, hợp trường học/đào tạo doanh nghiệp"]),

# ---------- Y tế ----------
"openemr/openemr": dict(
    f=["Hồ sơ bệnh án điện tử", "Lịch hẹn, kê đơn, thanh toán", "Cổng bệnh nhân"],
    s=["EMR mã nguồn mở phổ biến nhất", "Dữ liệu sức khỏe là dữ liệu nhạy cảm — tuân thủ chặt luật dữ liệu VN"]),

# ---------- Trợ lý cá nhân ----------
"agentscope-ai/qwenpaw": dict(
    f=["Trợ lý AI cá nhân, cài một chạm trên Windows/macOS", "Kết nối nhiều app chat", "Hộp cát an toàn, kiểm soát công cụ, chặn truy cập file nhạy cảm"],
    s=["Mạnh về bảo mật agent; là trợ lý cá nhân, không phải phần mềm cho SME"]),
"hkuds/nanobot": dict(
    f=["Agent cá nhân nhẹ, chạy web hoặc terminal", "Kết nối Telegram, Slack, WeChat, email...", "Đọc PDF, Word, Excel; tác vụ định kỳ"],
    s=["Gọn, dễ tùy biến — có thể làm nền bot Zalo cho chủ shop"]),
}
