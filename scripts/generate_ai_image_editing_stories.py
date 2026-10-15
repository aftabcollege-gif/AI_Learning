from pathlib import Path
from html import escape
import textwrap

W, H = 1080, 1920
OUT = Path('stories/2026-09-17')
OUT.mkdir(parents=True, exist_ok=True)

IDENTITY_ANCHOR = (
    'Use the uploaded reference image as the permanent identity anchor. Preserve the exact facial identity, '
    'facial structure, proportions, eye shape, eyebrows, nose, lips, jawline, chin, skin tone, apparent age '
    'and distinctive facial characteristics. The person must remain instantly recognizable as the same individual. '
    'Do not alter identity, ethnicity, age or face shape. Change only the explicitly requested elements.'
)

LEVELS = {
    **{i: 'سطح 1 • پایه' for i in range(1, 6)},
    **{i: 'سطح 2 • سوژه' for i in range(6, 12)},
    **{i: 'سطح 3 • محیط' for i in range(12, 16)},
    **{i: 'سطح 4 • سبک' for i in range(16, 21)},
    **{i: 'سطح 5 • شرایط تصویر' for i in range(21, 26)},
    **{i: 'سطح 6 • کاربرد حرفه‌ای' for i in range(26, 29)},
    **{i: 'سطح 7 • حرفه‌ای' for i in range(29, 31)},
}

PALETTES = {
    'emerald': ('#66e6bf', '#35d0a0', '#23a9ff'),
    'ice': ('#9ad8ff', '#23a9ff', '#66e6bf'),
    'gold': ('#f6d06b', '#d79a2b', '#66e6bf'),
    'violet': ('#c39bff', '#9a6dff', '#35d0a0'),
    'sunset': ('#ffb26b', '#ff7f50', '#f6d06b'),
    'silver': ('#dce5ea', '#9cb3c2', '#66e6bf'),
}

STORIES = [
    {'num': 1, 'slug': 'Story_01_Light_Correction', 'title': 'اصلاح نور', 'palette': 'emerald', 'layout': 'grid5', 'subtitle': 'نور ناهماهنگ را طبیعی و کنترل‌شده اصلاح کن.', 'tip': 'اول نور را اصلاح کن؛ بعد سراغ رنگ و افکت برو.', 'examples': [
        ('عکس تیره', 'Brighten the image naturally, recover facial details, balance exposure, preserve identity and skin texture.'),
        ('نور نامتوازن', 'Balance uneven lighting across the face, preserve natural shadows, skin texture and exact facial identity.'),
        ('پس‌زمینه اوور', 'Reduce background highlights, recover overexposed areas and maintain natural facial exposure.'),
        ('تصویر تخت', 'Add subtle contrast and dimensional lighting while preserving natural skin tones and facial identity.'),
        ('نور استودیویی', 'Transform the existing lighting into clean professional studio lighting while preserving the subject\'s identity.'),
    ]},
    {'num': 2, 'slug': 'Story_02_Professional_Lighting', 'title': 'نورپردازی حرفه‌ای', 'palette': 'ice', 'layout': 'grid5', 'subtitle': 'با نوع نور، حس و عمق پرتره را طراحی کن.', 'tip': 'نوع نور می‌تواند حس تصویر را کاملاً تغییر دهد.', 'examples': [
        ('Rembrandt', 'Create subtle Rembrandt lighting on the face, cinematic shadows, preserve exact identity.'),
        ('Softbox', 'Create soft professional softbox lighting, even facial illumination, natural skin texture.'),
        ('Butterfly', 'Create elegant butterfly lighting, soft frontal illumination, preserve facial structure and identity.'),
        ('Rim', 'Add subtle cinematic rim light around the subject while preserving the original face.'),
        ('Cinematic', 'Create dramatic cinematic lighting with controlled highlights and shadows, preserve identity.'),
    ]},
    {'num': 3, 'slug': 'Story_03_Time_Weather', 'title': 'تغییر زمان و شرایط نور', 'palette': 'sunset', 'layout': 'timeline5', 'subtitle': 'زمان روز را با نور واقعی، نه فقط رنگ، عوض کن.', 'tip': 'برای تغییر زمان، فقط رنگ را عوض نکن؛ جهت و شدت نور را هم تغییر بده.', 'examples': [
        ('ظهر ← گلدن‌آور', 'Transform harsh midday lighting into warm golden-hour sunlight, preserve identity.'),
        ('روز ← غروب', 'Change daylight into cinematic sunset lighting with warm horizon glow, preserve identity.'),
        ('روز ← شب', 'Transform the scene from daytime into realistic nighttime lighting, preserve subject identity.'),
        ('ابری ← آفتابی', 'Transform overcast lighting into natural sunny daylight while preserving realistic shadows.'),
        ('سرد ← گرم', 'Shift the lighting from cool tones to warm cinematic illumination, preserve natural skin.'),
    ]},
    {'num': 4, 'slug': 'Story_04_Camera_Angle', 'title': 'تغییر زاویه دوربین', 'palette': 'emerald', 'layout': 'grid5', 'subtitle': 'زاویه درست یعنی پرسپکتیو درستِ چهره.', 'tip': 'زاویه دوربین فقط جهت نگاه نیست؛ پرسپکتیو صورت را هم تغییر می‌دهد.', 'examples': [
        ('Front', 'Create a straight-on front camera angle, preserve exact facial identity and proportions.'),
        ('3/4 View', 'Change the camera angle to a natural three-quarter view, preserve facial identity.'),
        ('Side Profile', 'Create a realistic side-profile camera angle while preserving the subject\'s identity.'),
        ('Low Angle', 'Change camera perspective to a subtle low angle, preserve face and body proportions.'),
        ('High Angle', 'Create a natural high-angle portrait perspective, preserve exact identity.'),
    ]},
    {'num': 5, 'slug': 'Story_05_Lens', 'title': 'لنز و فاصله دوربین', 'palette': 'ice', 'layout': 'grid5', 'subtitle': 'لنز، حس فاصله و شخصیت پرتره را تعیین می‌کند.', 'tip': 'لنز مناسب می‌تواند پرتره را طبیعی‌تر یا سینمایی‌تر کند.', 'examples': [
        ('24mm', 'Simulate a 24mm wide-angle lens, realistic perspective, preserve identity.'),
        ('35mm', 'Simulate a natural 35mm documentary lens perspective, preserve identity.'),
        ('50mm', 'Simulate a natural 50mm portrait perspective, preserve facial proportions.'),
        ('85mm', 'Simulate an 85mm professional portrait lens with natural compression and shallow depth of field.'),
        ('135mm', 'Simulate a 135mm telephoto portrait lens with elegant background compression.'),
    ]},
    {'num': 6, 'slug': 'Story_06_Clothing', 'title': 'تغییر لباس', 'palette': 'gold', 'layout': 'editorial5', 'subtitle': 'لباس را عوض کن، نه هویت را.', 'tip': 'برای تغییر لباس، فقط نوع لباس را مشخص کن؛ جنس و رنگ را هم تعیین کن.', 'examples': [
        ('Formal Suit', 'Replace the clothing with an elegant dark formal suit, preserve face and body proportions.'),
        ('Smart Casual', 'Change clothing to premium smart-casual style, preserve identity and body proportions.'),
        ('Executive', 'Dress the subject in a sophisticated executive business outfit, preserve exact identity.'),
        ('Streetwear', 'Replace clothing with modern premium streetwear, preserve face and body proportions.'),
        ('Luxury Fashion', 'Dress the subject in high-end luxury fashion styling, preserve exact facial identity.'),
    ]},
    {'num': 7, 'slug': 'Story_07_Hairstyle', 'title': 'تغییر مدل مو', 'palette': 'violet', 'layout': 'grid6', 'subtitle': 'مدل مو را دقیق تعریف کن: طول، بافت، جهت.', 'tip': 'در پرامپت مو، مدل، طول، بافت و حالت را دقیق بنویس.', 'examples': [
        ('Classic Short', 'Change hairstyle to a clean classic short haircut, preserve exact face and identity.'),
        ('Modern Cut', 'Change hairstyle to a modern textured haircut, preserve facial structure.'),
        ('Longer Hair', 'Give the subject naturally longer styled hair, preserve exact facial identity.'),
        ('Side Part', 'Create a professional side-part hairstyle, preserve face and identity.'),
        ('Textured', 'Create a natural textured hairstyle with realistic hair strands, preserve identity.'),
        ('Formal', 'Create an elegant formal hairstyle suitable for a professional portrait.'),
    ]},
    {'num': 8, 'slug': 'Story_08_Expression', 'title': 'تغییر حالت چهره', 'palette': 'emerald', 'layout': 'grid6', 'subtitle': 'حالت چهره را تغییر بده، نه ساختار صورت را.', 'tip': 'Expression را تغییر بده، نه خود چهره را.', 'examples': [
        ('Neutral', 'Change facial expression to a natural neutral expression, preserve exact identity.'),
        ('Smile', 'Create a subtle natural smile, preserve exact facial structure and identity.'),
        ('Serious', 'Create a confident serious expression, preserve facial identity.'),
        ('Thoughtful', 'Create a natural thoughtful expression, preserve exact facial features.'),
        ('Surprised', 'Create a subtle surprised expression, preserve identity and facial proportions.'),
        ('Confident', 'Create a confident professional expression, preserve exact identity.'),
    ]},
    {'num': 9, 'slug': 'Story_09_Skin_Retouch', 'title': 'روتوش طبیعی پوست', 'palette': 'gold', 'layout': 'grid5', 'subtitle': 'روتوش خوب دیده نمی‌شود؛ فقط نتیجه‌اش دیده می‌شود.', 'tip': 'Retouch حرفه‌ای یعنی پوست بهتر؛ نه پوست پلاستیکی.', 'examples': [
        ('Blemishes', 'Remove temporary facial blemishes naturally, preserve skin texture and identity.'),
        ('Skin Spots', 'Reduce temporary skin spots while preserving realistic skin texture.'),
        ('Redness', 'Reduce uneven facial redness naturally without changing skin tone.'),
        ('Tone Balance', 'Even out skin tone subtly while preserving natural pores and texture.'),
        ('Portrait Retouch', 'Apply professional natural portrait retouching, preserve pores, texture and exact identity.'),
    ]},
    {'num': 10, 'slug': 'Story_10_Face_Details', 'title': 'جزئیات صورت', 'palette': 'silver', 'layout': 'grid5', 'subtitle': 'جزئیات ظریف، واقع‌گرایی نهایی را می‌سازند.', 'tip': 'جزئیات کوچک بیشترین تأثیر را در واقعی‌بودن نتیجه دارند.', 'examples': [
        ('Eyebrows', 'Clean up eyebrow edges naturally while preserving their original shape and identity.'),
        ('Eyes', 'Enhance eye clarity and detail naturally, preserve exact eye shape.'),
        ('Beard', 'Clean and refine beard edges naturally, preserve facial identity.'),
        ('Lips', 'Enhance natural lip detail and texture without changing lip shape.'),
        ('Facial Detail', 'Enhance subtle facial details and texture while preserving exact identity.'),
    ]},
    {'num': 11, 'slug': 'Story_11_Accessories', 'title': 'افزودن اکسسوری', 'palette': 'violet', 'layout': 'grid6', 'subtitle': 'اکسسوری باید روی چهره و نور بنشیند.', 'tip': 'برای اکسسوری، جنس، اندازه، جای قرارگیری و انعکاس نور را مشخص کن.', 'examples': [
        ('Glasses', 'Add elegant realistic eyeglasses, preserve exact facial identity and proportions.'),
        ('Sunglasses', 'Add premium sunglasses with realistic reflections, preserve identity.'),
        ('Watch', 'Add a sophisticated wristwatch with realistic lighting and reflections.'),
        ('Headphones', 'Add modern premium headphones, preserve subject identity.'),
        ('Hat', 'Add a stylish realistic hat while preserving face and identity.'),
        ('Bracelet', 'Add a minimal premium bracelet with realistic material and lighting.'),
    ]},
    {'num': 12, 'slug': 'Story_12_Object_Removal', 'title': 'حذف اشیا', 'palette': 'ice', 'layout': 'grid5', 'subtitle': 'حذف تمیز یعنی بازسازی طبیعی اطراف.', 'tip': 'بعد از حذف شیء، حتماً از AI بخواه پس‌زمینه را طبیعی بازسازی کند.', 'examples': [
        ('شخص مزاحم', 'Remove the unwanted person in the background and reconstruct the scene naturally.'),
        ('کابل', 'Remove the visible cable and reconstruct the background naturally.'),
        ('تابلو', 'Remove the distracting sign and seamlessly reconstruct the background.'),
        ('شیء روی میز', 'Remove the unwanted desk object while preserving surrounding details.'),
        ('عنصر اضافی', 'Remove the distracting background element and create a clean realistic reconstruction.'),
    ]},
    {'num': 13, 'slug': 'Story_13_Object_Addition', 'title': 'اضافه کردن اشیا', 'palette': 'emerald', 'layout': 'grid6', 'subtitle': 'شیء جدید باید پرسپکتیو و نور خودش را داشته باشد.', 'tip': 'برای افزودن شیء، جای دقیق، اندازه، نور و پرسپکتیو را تعیین کن.', 'examples': [
        ('Laptop', 'Add a premium laptop naturally on the desk with realistic perspective and lighting.'),
        ('Smartphone', 'Add a modern smartphone naturally into the scene with realistic reflections.'),
        ('Coffee', 'Add a realistic coffee cup with matching perspective and lighting.'),
        ('Camera', 'Add a professional camera naturally into the scene with realistic shadows.'),
        ('Book', 'Add an elegant book with realistic placement and lighting.'),
        ('Plant', 'Add a modern indoor plant naturally into the background.'),
    ]},
    {'num': 14, 'slug': 'Story_14_Background', 'title': 'تعویض پس‌زمینه', 'palette': 'violet', 'layout': 'grid5', 'subtitle': 'پس‌زمینه جدید باید با نور سوژه هماهنگ شود.', 'tip': 'پس‌زمینه باید با نور سوژه هماهنگ باشد.', 'examples': [
        ('Modern Office', 'Replace the background with a premium modern office, preserve subject identity.'),
        ('Luxury Studio', 'Place the subject inside a sophisticated luxury photography studio.'),
        ('Urban Street', 'Replace the background with a cinematic modern urban street.'),
        ('Nature', 'Place the subject in a beautiful realistic natural environment.'),
        ('Modern City', 'Place the subject in a futuristic modern city environment with cinematic lighting.'),
    ]},
    {'num': 15, 'slug': 'Story_15_Location', 'title': 'انتقال به مکان‌های مختلف', 'palette': 'sunset', 'layout': 'grid5', 'subtitle': 'لوکیشن واقعی با نور و سایه واقعی باورپذیر می‌شود.', 'tip': 'تعویض لوکیشن وقتی واقعی است که نور، سایه و پرسپکتیو هم هماهنگ شوند.', 'examples': [
        ('Tehran', 'Place the subject naturally in a recognizable modern Tehran environment, preserve identity.'),
        ('New York', 'Place the subject in a realistic New York City street environment, preserve identity.'),
        ('Paris', 'Place the subject in an elegant Parisian environment with realistic perspective.'),
        ('Beach', 'Place the subject naturally on a beautiful realistic beach.'),
        ('Mountain', 'Place the subject in a dramatic mountain environment with realistic lighting.'),
    ]},
    {'num': 16, 'slug': 'Story_16_Cinematic', 'title': 'ادیت سینمایی', 'palette': 'violet', 'layout': 'grid5', 'subtitle': 'سینمایی یعنی داستان در نور و رنگ.', 'tip': 'ادیت سینمایی یعنی نور، رنگ، عمق و داستان؛ نه فقط فیلتر.', 'examples': [
        ('Drama', 'Create a cinematic dramatic color grade and lighting while preserving exact identity.'),
        ('Thriller', 'Create a dark cinematic thriller atmosphere with controlled contrast, preserve identity.'),
        ('Action', 'Create an energetic cinematic action-movie atmosphere with realistic lighting.'),
        ('Sci-Fi', 'Transform the environment into a cinematic futuristic sci-fi scene, preserve identity.'),
        ('Hollywood', 'Create a premium cinematic Hollywood-style portrait while preserving exact facial identity.'),
    ]},
    {'num': 17, 'slug': 'Story_17_Professional_Portrait', 'title': 'پرتره حرفه‌ای', 'palette': 'silver', 'layout': 'grid5', 'subtitle': 'پرتره حرفه‌ای باید اعتماد بسازد.', 'tip': 'یک پرتره حرفه‌ای باید اعتماد ایجاد کند، نه فقط زیبا باشد.', 'examples': [
        ('Corporate', 'Create a polished corporate portrait with professional studio lighting, preserve identity.'),
        ('LinkedIn', 'Create a professional LinkedIn portrait, clean background, natural lighting, preserve identity.'),
        ('Executive', 'Create a sophisticated executive portrait with premium studio lighting.'),
        ('Magazine', 'Create a high-end editorial magazine portrait, preserve exact identity.'),
        ('Studio', 'Create a premium professional studio portrait with controlled lighting and realistic skin.'),
    ]},
    {'num': 18, 'slug': 'Story_18_Advertising', 'title': 'عکاسی تبلیغاتی', 'palette': 'gold', 'layout': 'grid5', 'subtitle': 'عکس تبلیغاتی باید پیام را در یک نگاه منتقل کند.', 'tip': 'در تبلیغات، تصویر باید یک پیام مشخص منتقل کند.', 'examples': [
        ('Fashion', 'Create a premium fashion advertising photograph with editorial lighting, preserve identity.'),
        ('Technology', 'Create a futuristic technology advertising scene with premium cinematic lighting.'),
        ('Luxury', 'Create a sophisticated luxury advertising photograph with elegant lighting.'),
        ('Lifestyle', 'Create a premium lifestyle advertising scene with natural cinematic lighting.'),
        ('Personal Brand', 'Create a premium personal-brand campaign image, preserve exact identity.'),
    ]},
    {'num': 19, 'slug': 'Story_19_Cartoon', 'title': 'تبدیل کارتونی', 'palette': 'violet', 'layout': 'grid5', 'subtitle': 'استایل کارتونی را عوض کن، هویت را نه.', 'tip': 'استایل را تغییر بده، اما هویت شخصیت را حفظ کن.', 'examples': [
        ('3D Cartoon', 'Transform the image into a polished 3D cartoon style while preserving recognizable identity.'),
        ('Comic', 'Transform the image into a premium comic-book illustration while preserving identity.'),
        ('Anime', 'Transform the image into a high-quality anime-inspired illustration while preserving recognizable facial features.'),
        ('Clay', 'Transform the subject into a detailed clay-style character while preserving recognizable identity.'),
        ('Stylized', 'Transform the image into a sophisticated stylized digital illustration while preserving identity.'),
    ]},
    {'num': 20, 'slug': 'Story_20_Artistic', 'title': 'تبدیل هنری', 'palette': 'sunset', 'layout': 'grid5', 'subtitle': 'سبک هنری دقیق، خروجی کنترل‌شده می‌سازد.', 'tip': 'استایل هنری را دقیق تعریف کن تا نتیجه تصادفی کمتر شود.', 'examples': [
        ('Oil Painting', 'Transform the image into a detailed classical oil painting while preserving recognizable identity.'),
        ('Watercolor', 'Transform the image into an elegant watercolor artwork while preserving facial identity.'),
        ('Pencil', 'Transform the image into a detailed graphite pencil portrait while preserving identity.'),
        ('Digital Art', 'Transform the image into premium digital artwork while preserving recognizable facial features.'),
        ('Concept Art', 'Transform the image into cinematic concept art while preserving the subject\'s identity.'),
    ]},
    {'num': 21, 'slug': 'Story_21_Seasons', 'title': 'تغییر فصل', 'palette': 'sunset', 'layout': 'grid4', 'subtitle': 'فصل فقط رنگ نیست؛ محیط و لباس هم هست.', 'tip': 'فصل فقط رنگ نیست؛ پوشش، نور و محیط هم باید تغییر کند.', 'examples': [
        ('Spring', 'Transform the environment into a beautiful spring setting with fresh greenery and soft light.'),
        ('Summer', 'Create a bright realistic summer environment with natural sunlight.'),
        ('Autumn', 'Transform the scene into a cinematic autumn environment with warm foliage.'),
        ('Winter', 'Transform the environment into a realistic winter scene with subtle snow.'),
    ]},
    {'num': 22, 'slug': 'Story_22_Weather', 'title': 'تغییر آب‌وهوا', 'palette': 'ice', 'layout': 'grid5', 'subtitle': 'آب‌وهوا باید روی نور و سطوح اثر بگذارد.', 'tip': 'آب‌وهوای واقعی باید روی نور، زمین و بازتاب‌ها اثر بگذارد.', 'examples': [
        ('Sunny', 'Transform the scene into bright realistic sunny weather with natural sunlight and crisp shadows, preserve identity.'),
        ('Rainy', 'Transform the scene into realistic rainy weather with wet surfaces and reflections, preserve identity.'),
        ('Snowy', 'Transform the scene into realistic snowy weather with subtle snowfall and cold natural light, preserve identity.'),
        ('Foggy', 'Transform the scene into atmospheric realistic fog with soft diffused lighting, preserve identity.'),
        ('Stormy', 'Transform the scene into a dramatic realistic storm atmosphere with dark clouds and cinematic lighting, preserve identity.'),
    ]},
    {'num': 23, 'slug': 'Story_23_Color_Grade', 'title': 'کالرگرید', 'palette': 'violet', 'layout': 'grid5', 'subtitle': 'کالرگرید باید حس تصویر را بسازد، نه اینکه جزئیات را خفه کند.', 'tip': 'کالرگرید باید حس بسازد، نه اینکه جزئیات تصویر را نابود کند.', 'examples': [
        ('Warm', 'Apply a warm cinematic color grade with rich skin tones while preserving natural detail and identity.'),
        ('Cool', 'Apply a cool modern color grade with clean blue tones, preserve natural skin and identity.'),
        ('Teal & Orange', 'Apply a cinematic teal and orange color grade while preserving realistic skin texture and exact identity.'),
        ('Black & White', 'Convert the image to elegant high-contrast black and white while preserving detail.'),
        ('Vintage', 'Apply an elegant vintage film color grade with subtle fade and preserved detail, maintain identity.'),
    ]},
    {'num': 24, 'slug': 'Story_24_Enhancement', 'title': 'افزایش کیفیت', 'palette': 'silver', 'layout': 'grid5', 'subtitle': 'کیفیت بهتر یعنی جزئیات واضح‌تر، نه لبه‌های مصنوعی.', 'tip': 'بزرگ‌نمایی تصویر با شارپ‌کردن یکی نیست.', 'examples': [
        ('Upscale', 'Upscale the image cleanly, increase resolution and fine detail while preserving identity and natural texture.'),
        ('Sharpen', 'Improve image sharpness naturally without creating artificial edges.'),
        ('Recover Details', 'Recover subtle facial and clothing details naturally without changing identity or texture.'),
        ('Noise Reduction', 'Reduce digital noise cleanly while preserving natural detail and skin texture.'),
        ('Detail Restoration', 'Restore lost image details naturally and improve clarity without overprocessing.'),
    ]},
    {'num': 25, 'slug': 'Story_25_Restoration', 'title': 'ترمیم عکس قدیمی', 'palette': 'gold', 'layout': 'grid5', 'subtitle': 'بازسازی عکس یعنی احیا، نه بازطراحی کامل.', 'tip': 'در بازسازی، هدف احیای عکس است؛ نه طراحی دوباره.', 'examples': [
        ('Old Blurry', 'Restore this old blurry photo with improved clarity while preserving the original identity and natural appearance.'),
        ('Damaged', 'Repair damaged areas, tears and scratches naturally while preserving the original identity.'),
        ('Faded', 'Restore faded colors and contrast while maintaining the original look and facial identity.'),
        ('Low Light', 'Recover a low-light old photo, improve exposure and detail while preserving authenticity.'),
        ('Black & White', 'Restore the black and white photo, recover contrast and facial detail while preserving authenticity.'),
    ]},
    {'num': 26, 'slug': 'Story_26_Pose', 'title': 'تغییر ژست', 'palette': 'emerald', 'layout': 'grid5', 'subtitle': 'ژست را عوض کن؛ آناتومی را حفظ کن.', 'tip': 'در تغییر ژست باید آناتومی و تناسب بدن حفظ شود.', 'examples': [
        ('Standing', 'Change the pose to a confident standing pose, preserve anatomy, proportions and exact identity.'),
        ('Sitting', 'Change the pose to a natural seated pose, preserve anatomy, proportions and identity.'),
        ('Walking', 'Create a realistic walking pose, preserve anatomy, proportions and exact identity.'),
        ('Arms Crossed', 'Change the pose to natural crossed arms, preserve anatomy, body proportions and identity.'),
        ('Hands in Pocket', 'Create a relaxed hands-in-pocket pose, preserve anatomy, proportions and identity.'),
    ]},
    {'num': 27, 'slug': 'Story_27_Work_Environment', 'title': 'محیط کاری', 'palette': 'silver', 'layout': 'grid5', 'subtitle': 'محیط کاری باید با برند شخصی هماهنگ باشد.', 'tip': 'محیط کاری باید با لباس، نور و شخصیت تصویر هماهنگ باشد.', 'examples': [
        ('Modern Office', 'Place the subject in a premium modern office workspace, preserve identity and realistic lighting.'),
        ('Executive Office', 'Place the subject in a sophisticated executive office environment, preserve exact identity.'),
        ('Meeting Room', 'Place the subject naturally in a professional meeting room, preserve identity and perspective.'),
        ('Startup', 'Place the subject in a modern startup work environment with natural professional lighting, preserve identity.'),
        ('Creative Studio', 'Place the subject in a stylish creative studio workspace, preserve identity and realistic scene integration.'),
    ]},
    {'num': 28, 'slug': 'Story_28_Social_Media', 'title': 'تبدیل برای شبکه‌های اجتماعی', 'palette': 'violet', 'layout': 'grid5', 'subtitle': 'هر پلتفرم، زبان بصری خودش را دارد.', 'tip': 'هر پلتفرم زبان بصری متفاوتی دارد.', 'examples': [
        ('Instagram Profile', 'Create a polished Instagram profile portrait with clean composition, trendy lighting and exact identity.'),
        ('LinkedIn', 'Create a professional LinkedIn-ready portrait with clean background, confident look and exact identity.'),
        ('Personal Brand', 'Create a premium personal-brand portrait with cinematic lighting, preserve exact identity.'),
        ('Professional Portrait', 'Create a refined professional portrait optimized for social media visibility, preserve identity.'),
        ('Creator Profile', 'Create a modern creator-profile image with clean lighting, strong presence and exact identity.'),
    ]},
    {'num': 29, 'slug': 'Story_29_Multi_Edit', 'title': 'ویرایش چندمرحله‌ای', 'palette': 'gold', 'layout': 'grid5', 'subtitle': 'چند ادیت را با ترتیب درست در یک پرامپت بچین.', 'tip': 'برای ادیت‌های پیچیده، پرامپت را به بخش‌های جدا تقسیم کن: سوژه، تغییر، محیط، نور، استایل، هویت.', 'examples': [
        ('Suit + Office', 'Change clothing to a dark formal suit, place the subject in a modern office, add cinematic soft lighting and a subtle cool color grade, preserve exact identity.'),
        ('Hair + Casual', 'Create a modern hairstyle, change clothing to premium smart casual, use a three-quarter camera angle and soft studio lighting, preserve exact identity.'),
        ('Rainy Paris', 'Place the subject in a rainy Paris street, add an elegant coat and cinematic evening lighting, preserve exact identity.'),
        ('Studio Cleanup', 'Remove the distracting background elements, replace the environment with a luxury studio and apply a cinematic warm color grade, preserve identity.'),
        ('Executive Master', 'Create a confident standing pose, dress the subject in a dark executive suit, place them in a modern office and use dramatic professional lighting, preserve exact identity.'),
    ]},
    {'num': 30, 'slug': 'Story_30_Master_Edit', 'title': 'MASTER AI EDIT', 'palette': 'gold', 'layout': 'process6', 'subtitle': 'همه تکنیک‌ها را در یک ادیت نهایی جمع کن.', 'tip': 'ادیت نهایی را ماژول‌بندی کن: سوژه، لباس، ژست، محیط، نور، استایل، هویت.', 'examples': [
        ('Professional', 'Create a premium professional portrait with modern executive clothing, soft studio lighting and exact facial identity.'),
        ('Cinematic', 'Create a cinematic personal portrait with dramatic lighting, subtle rim light and exact identity.'),
        ('Luxury', 'Create a luxury editorial portrait with premium styling, elegant lighting and preserved identity.'),
        ('Social Media', 'Create a polished social-media personal brand portrait with clean framing, modern lighting and exact identity.'),
        ('Creative', 'Create a creative stylized portrait with artistic background, controlled color and exact identity.'),
        ('Complete Transformation', 'Create a premium cinematic personal-brand portrait: modern executive clothing, confident pose, three-quarter camera angle, luxury studio environment, soft key light, subtle rim light, cinematic color grade, realistic skin texture and exact facial identity.'),
    ]},
]


def wrap(text, width):
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or ['']


def text_block(x, y, lines, size, fill, anchor='start', weight='normal', family='DejaVu Sans', gap=1.35):
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" font-family="{family}" font-size="{size}" font-weight="{weight}">']
    for i, line in enumerate(lines):
        dy = '0' if i == 0 else str(round(size * gap, 1))
        out.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    out.append('</text>')
    return ''.join(out)


def svg_defs(a1, a2, a3):
    return f'''
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#051511"/>
    <stop offset="0.55" stop-color="#0c2e26"/>
    <stop offset="1" stop-color="#020806"/>
  </linearGradient>
  <radialGradient id="glowA" cx="0.2" cy="0.1" r="0.8">
    <stop stop-color="{a1}" stop-opacity="0.18"/>
    <stop offset="1" stop-color="{a1}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowB" cx="0.9" cy="0.2" r="0.9">
    <stop stop-color="{a2}" stop-opacity="0.12"/>
    <stop offset="1" stop-color="{a2}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="{a1}"/>
    <stop offset="1" stop-color="{a2}"/>
  </linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="#f6d06b"/>
    <stop offset="1" stop-color="#b98424"/>
  </linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#10241f" stop-opacity="0.95"/>
    <stop offset="1" stop-color="#06110f" stop-opacity="0.97"/>
  </linearGradient>
  <linearGradient id="panelBefore" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#16211f"/>
    <stop offset="1" stop-color="#0a1110"/>
  </linearGradient>
  <linearGradient id="panelAfter" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#173028"/>
    <stop offset="1" stop-color="#0d1815"/>
  </linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="#000000" flood-opacity="0.35"/>
  </filter>
</defs>
'''


def chips(story, a1):
    count = len(story['examples'])
    return (
        f'<rect x="60" y="185" width="220" height="46" rx="23" fill="#0c1e1a" stroke="{a1}" stroke-opacity="0.65"/>'
        f'<text x="170" y="216" text-anchor="middle" fill="{a1}" font-family="DejaVu Sans" font-size="22" font-weight="bold">{LEVELS[story["num"]]}</text>'
        f'<rect x="790" y="185" width="230" height="46" rx="23" fill="#0c1e1a" stroke="#f6d06b" stroke-opacity="0.7"/>'
        f'<text x="905" y="216" text-anchor="middle" fill="#f6d06b" font-family="DejaVu Sans" font-size="22" font-weight="bold">{count} Before / After</text>'
    )


def subject_parts(style_mod='photo', hair=0, expr=0, cloth=0, accessory=None, pose=0, angle=0):
    # Returns snippets in local group coordinates 0..100 x 0..120
    jacket_colors = [('#0b0f14', '#d8dde4', '#19335b'), ('#546655', '#efece6', '#bfa25a'), ('#161f30', '#d8dde5', '#10294e'), ('#1d2027', '#455678', '#66e6bf'), ('#1a1218', '#efe1c6', '#b98424')]
    jacket, shirt, tie = jacket_colors[cloth % len(jacket_colors)]
    hair_paths = [
        'M 36 23 Q 50 5 64 23 L 60 34 Q 50 29 40 34 Z',
        'M 35 24 Q 42 8 51 14 Q 58 5 66 22 L 60 34 Q 50 30 40 34 Z',
        'M 34 24 Q 50 4 66 24 L 62 38 Q 50 34 38 38 Z',
        'M 35 23 Q 47 8 65 20 L 61 33 Q 50 28 40 34 Z',
        'M 34 24 Q 50 6 66 24 L 58 31 Q 50 24 42 31 Z',
    ]
    mouths = [
        '<path d="M 43 56 Q 50 57 57 56" stroke="#6f4d41" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
        '<path d="M 42 55 Q 50 61 58 55" stroke="#6f4d41" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
        '<path d="M 43 57 Q 50 54 57 57" stroke="#6f4d41" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
        '<circle cx="50" cy="57" r="3.4" fill="none" stroke="#6f4d41" stroke-width="1.4"/>',
    ]
    body = [
        '<path d="M 28 74 Q 50 64 72 74 L 80 118 L 20 118 Z" fill="%s"/>' % jacket,
        '<path d="M 40 74 L 50 86 L 60 74 L 56 108 L 44 108 Z" fill="%s"/>' % shirt,
        '<path d="M 50 83 L 54 92 L 50 108 L 46 92 Z" fill="%s"/>' % tie,
    ]
    if pose == 1:
        body.append('<rect x="24" y="108" width="52" height="8" rx="4" fill="#34261b" opacity="0.8"/>')
    if pose == 2:
        body.append('<path d="M 28 85 Q 18 92 16 108" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
        body.append('<path d="M 72 85 Q 84 92 88 104" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
    elif pose == 3:
        body.append('<path d="M 24 86 Q 44 82 66 94" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
        body.append('<path d="M 76 86 Q 56 82 34 94" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
    elif pose == 4:
        body.append('<path d="M 24 86 Q 30 99 36 110" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
        body.append('<path d="M 76 86 Q 70 96 62 102" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
    else:
        body.append('<path d="M 24 86 Q 22 98 22 112" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)
        body.append('<path d="M 76 86 Q 78 97 78 110" stroke="%s" stroke-width="9" fill="none" stroke-linecap="round"/>' % jacket)

    face_style = ''
    face_fill = '#d4a087'
    beard_fill = '#251e1c'
    hair_fill = '#26201f'
    eye_fill = '#161414'
    extra = ''
    if style_mod == 'bw':
        face_fill, beard_fill, hair_fill = '#bfbfbf', '#5a5a5a', '#4d4d4d'
    elif style_mod == 'old':
        face_fill, beard_fill, hair_fill = '#b19371', '#705842', '#6d5844'
        extra += '<path d="M 12 18 L 88 102" stroke="#ead9ab" stroke-opacity="0.18"/><path d="M 25 10 L 18 90" stroke="#ead9ab" stroke-opacity="0.14"/>'
    elif style_mod == 'anime':
        face_fill, beard_fill, hair_fill = '#f1c5ae', '#2f2636', '#443a64'
    elif style_mod == 'comic':
        extra += '<path d="M 10 14 L 16 18 M 22 12 L 28 16 M 32 12 L 38 16 M 68 14 L 74 18 M 78 18 L 84 22" stroke="#ffffff" stroke-opacity="0.22"/>'
    elif style_mod == 'clay':
        face_fill, beard_fill, hair_fill = '#d8a98d', '#5f4432', '#7b6657'
    elif style_mod == 'water':
        extra += '<ellipse cx="42" cy="34" rx="30" ry="18" fill="#8bbcff" opacity="0.12"/>'
    elif style_mod == 'digital':
        extra += '<rect x="12" y="16" width="76" height="88" rx="12" fill="none" stroke="#7d7cff" stroke-opacity="0.25"/>'

    angle_t = {0:'',1:'translate(-3,0) scale(0.96,1)',2:'translate(-7,0) scale(0.88,1)',3:'translate(0,3) scale(1.02,1.04)',4:'translate(0,-3) scale(0.98,0.96)'}[angle]
    group_open = '<g>' if not angle_t else f'<g transform="{angle_t}">'
    out = [group_open]
    out.extend(body)
    out.append(f'<ellipse cx="50" cy="40" rx="15" ry="18" fill="{face_fill}"/>')
    out.append(f'<path d="{hair_paths[hair % len(hair_paths)]}" fill="{hair_fill}"/>')
    out.append('<path d="M 39 45 Q 50 68 61 45 Q 57 68 50 70 Q 43 68 39 45 Z" fill="%s"/>' % beard_fill)
    out.append('<path d="M 41 36 L 46 35 M 54 35 L 59 36" stroke="#1c1717" stroke-width="1.8" stroke-linecap="round"/>')
    out.append('<ellipse cx="44" cy="41" rx="2.3" ry="1.8" fill="%s"/><ellipse cx="56" cy="41" rx="2.3" ry="1.8" fill="%s"/>' % (eye_fill, eye_fill))
    out.append(mouths[expr % len(mouths)])
    out.append('<path d="M 50 42 Q 48 47 50 49" stroke="#8b6752" stroke-width="1.2" fill="none" stroke-linecap="round"/>')
    for dx in (-6, 0, 6):
        out.append(f'<path d="M {44+dx} 24 Q {46+dx} 29 {47+dx} 33" stroke="#a4aaad" stroke-width="1.7" stroke-linecap="round" opacity="0.75"/>')
    if accessory == 'glasses':
        out.append('<circle cx="44" cy="41" r="5.2" fill="none" stroke="#d9edf2" stroke-width="1.3"/><circle cx="56" cy="41" r="5.2" fill="none" stroke="#d9edf2" stroke-width="1.3"/><line x1="49" y1="41" x2="51" y2="41" stroke="#d9edf2" stroke-width="1.1"/>')
    elif accessory == 'sunglasses':
        out.append('<rect x="38" y="36" width="12" height="8" rx="3" fill="#0a0f18" opacity="0.9"/><rect x="50" y="36" width="12" height="8" rx="3" fill="#0a0f18" opacity="0.9"/><line x1="49" y1="40" x2="51" y2="40" stroke="#6fd6ff" stroke-width="1.1"/>')
    elif accessory == 'headphones':
        out.append('<path d="M 35 42 Q 35 28 50 26 Q 65 28 65 42" stroke="#d7d9e5" stroke-width="3" fill="none" opacity="0.9"/><rect x="31" y="42" width="6" height="13" rx="3" fill="#d7d9e5"/><rect x="63" y="42" width="6" height="13" rx="3" fill="#d7d9e5"/>')
    elif accessory == 'hat':
        out.append('<ellipse cx="50" cy="26" rx="20" ry="5" fill="#1f1a1d"/><rect x="39" y="14" width="22" height="13" rx="4" fill="#2e252a"/>')
    elif accessory == 'watch':
        out.append('<circle cx="22" cy="111" r="5" fill="#203d45" stroke="#d7d9e5" stroke-width="1.2"/>')
    elif accessory == 'bracelet':
        out.append('<path d="M 20 111 Q 22 114 25 111" stroke="#e6c67d" stroke-width="2.1" fill="none" stroke-linecap="round"/>')
    out.append(extra)
    out.append('</g>')
    return ''.join(out)


def draw_scene(story_num, ex_idx, stage, x, y, w, h, a1, a2):
    bg = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{("url(#panelBefore)" if stage==0 else "url(#panelAfter)")}"/>']
    # broad categories
    if story_num in (12, 13, 14, 15, 18, 21, 22, 27, 28, 29, 30):
        bg.append(f'<rect x="{x+8}" y="{y+8}" width="{w-16}" height="{h*0.52:.1f}" rx="12" fill="#dff7ff" opacity="{0.08 if stage==0 else 0.14}"/>')
        bg.append(f'<rect x="{x+10}" y="{y+h*0.68:.1f}" width="{w-20}" height="{h*0.18:.1f}" rx="10" fill="#0a1413" opacity="0.65"/>')
    if story_num in (14, 15, 16, 18, 21, 22):
        sky_colors = ['#26465a', '#3e334e', '#214941', '#5b3726', '#1a2942']
        bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{sky_colors[ex_idx % len(sky_colors)]}" opacity="{0.35 if stage==0 else 0.55}"/>')
    if story_num == 14:
        if ex_idx == 0:  # office
            for i in range(3):
                bg.append(f'<rect x="{x+12+i*(w-48)/3:.1f}" y="{y+14}" width="{(w-58)/3:.1f}" height="{h*0.28:.1f}" rx="8" fill="#e7fbff" opacity="0.12"/>')
        elif ex_idx == 1:
            bg.append(f'<circle cx="{x+w*0.5:.1f}" cy="{y+h*0.35:.1f}" r="{h*0.2:.1f}" fill="#f6d06b" opacity="0.18"/>')
        elif ex_idx == 2:
            for i in range(5):
                bg.append(f'<rect x="{x+15+i*(w-35)/5:.1f}" y="{y+h*0.35:.1f}" width="{(w-65)/5:.1f}" height="{h*0.42:.1f}" rx="4" fill="#d9f7f0" opacity="0.10"/>')
        elif ex_idx == 3:
            bg.append(f'<path d="M {x} {y+h*0.78:.1f} Q {x+w*0.3:.1f} {y+h*0.45:.1f} {x+w*0.62:.1f} {y+h*0.73:.1f} T {x+w} {y+h*0.65:.1f} L {x+w} {y+h} L {x} {y+h} Z" fill="#4c7a54" opacity="0.55"/>')
        else:
            for i in range(6):
                bg.append(f'<line x1="{x+10+i*w/6:.1f}" y1="{y+h*0.1:.1f}" x2="{x-20+i*w/6:.1f}" y2="{y+h*0.9:.1f}" stroke="#8a7bff" stroke-opacity="0.18"/>')
    if story_num == 15:
        if ex_idx == 0:
            bg.append(f'<path d="M {x+w*0.8:.1f} {y+h*0.2:.1f} L {x+w*0.8:.1f} {y+h*0.72:.1f}" stroke="#66e6bf" stroke-width="3" opacity="0.5"/><ellipse cx="{x+w*0.8:.1f}" cy="{y+h*0.25:.1f}" rx="16" ry="8" fill="none" stroke="#66e6bf" stroke-width="2" opacity="0.45"/>')
        elif ex_idx == 1:
            for i,hh in enumerate([0.22,0.34,0.26,0.44,0.3]):
                bg.append(f'<rect x="{x+16+i*(w-46)/5:.1f}" y="{y+h*(0.72-hh):.1f}" width="{(w-68)/5:.1f}" height="{h*hh:.1f}" rx="4" fill="#ecf7ff" opacity="0.10"/>')
        elif ex_idx == 2:
            cx=x+w*0.8; bg.append(f'<path d="M {cx-12:.1f} {y+h*0.72:.1f} L {cx:.1f} {y+h*0.18:.1f} L {cx+12:.1f} {y+h*0.72:.1f}" stroke="#f6d06b" stroke-width="2.4" fill="none" opacity="0.55"/>')
        elif ex_idx == 3:
            bg.append(f'<rect x="{x}" y="{y+h*0.56:.1f}" width="{w}" height="{h*0.16:.1f}" fill="#2baed1" opacity="0.55"/><rect x="{x}" y="{y+h*0.72:.1f}" width="{w}" height="{h*0.28:.1f}" fill="#b68a53" opacity="0.45"/>')
        else:
            for cx in (x+w*0.25, x+w*0.55, x+w*0.82):
                bg.append(f'<path d="M {cx-24:.1f} {y+h*0.74:.1f} L {cx:.1f} {y+h*0.42:.1f} L {cx+24:.1f} {y+h*0.74:.1f} Z" fill="#93a2af" opacity="0.55"/>')
    if story_num == 21:
        season_colors = ['#69c16a', '#ffe37a', '#d1773c', '#cfdff5']
        bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{season_colors[ex_idx]}" opacity="{0.18 if stage==0 else 0.25}"/>')
        if ex_idx == 3:
            for i in range(16):
                sx = x + 10 + (i * 17 % int(w-20))
                sy = y + 10 + (i * 23 % int(h-25))
                bg.append(f'<circle cx="{sx}" cy="{sy}" r="1.8" fill="#eef6ff" opacity="0.75"/>')
    if story_num == 22:
        if ex_idx == 1:
            for i in range(10):
                sx = x + 12 + i * (w-24)/9
                bg.append(f'<line x1="{sx:.1f}" y1="{y+18:.1f}" x2="{sx-12:.1f}" y2="{y+h-18:.1f}" stroke="#9bd3ff" stroke-opacity="0.45"/>')
        elif ex_idx == 2:
            for i in range(16):
                sx = x + 10 + (i * 23 % int(w-20))
                sy = y + 10 + (i * 19 % int(h-25))
                bg.append(f'<circle cx="{sx}" cy="{sy}" r="1.8" fill="#eef6ff" opacity="0.8"/>')
        elif ex_idx == 3:
            bg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" opacity="0.12"/>')
        elif ex_idx == 4:
            bg.append(f'<path d="M {x+w*0.78:.1f} {y+h*0.2:.1f} L {x+w*0.72:.1f} {y+h*0.45:.1f} L {x+w*0.82:.1f} {y+h*0.45:.1f} L {x+w*0.76:.1f} {y+h*0.72:.1f}" stroke="#f6d06b" stroke-width="3" fill="none" opacity="0.7"/>')
    return ''.join(bg)


def grade_overlay(story_num, ex_idx, stage, x, y, w, h):
    if stage == 0:
        return ''
    if story_num == 1:
        fills = ['#ffffff22', '#ffcc8855', '#88ddff33', '#f6d06b33', '#d8f7ff33']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    if story_num == 2:
        return ['<path d="M {x} {y} H {x2} V {y2}"/>'.format(x=x,y=y,x2=x+w*0.55,y2=y+h), ''][1-1]
    if story_num == 3:
        fills = ['#ffcc6640', '#ff8e5a40', '#526cff30', '#ffe76a25', '#ffb16c35']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    if story_num == 16:
        fills = ['#963cff33', '#0a132a66', '#ff7f5033', '#6f7cff33', '#f6d06b2b']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    if story_num == 19:
        fills = ['#96a6ff22', '#ffffff18', '#ff9dd622', '#ffcb8d22', '#7affd722']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    if story_num == 20:
        fills = ['#b9842422', '#7bc8ff20', '#ffffff16', '#7d7cff20', '#ff986620']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    if story_num == 23:
        fills = ['#ffb16c30', '#7dbbff28', '#35d0a020', '#ffffff10', '#d6a56528']
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fills[ex_idx]}"/>'
    return ''


def preview(story, ex_idx, stage, x, y, w, h, a1, a2, a3):
    style_mod = 'photo'
    hair = ex_idx % 5
    expr = 0
    cloth = 0
    accessory = None
    pose = 0
    angle = 0
    num = story['num']
    if num == 4 and stage == 1:
        angle = [0,1,2,3,4][ex_idx]
    if num == 5 and stage == 1:
        angle = [3,1,0,2,4][ex_idx]
    if num == 6 and stage == 1:
        cloth = ex_idx
    if num == 7 and stage == 1:
        hair = ex_idx
    if num == 8 and stage == 1:
        expr = ex_idx if ex_idx < 4 else (1 if ex_idx == 5 else 3)
    if num == 9 and stage == 0:
        style_mod = 'photo'
    if num == 11 and stage == 1:
        accessory = ['glasses', 'sunglasses', 'watch', 'headphones', 'hat', 'bracelet'][ex_idx]
    if num == 16 and stage == 1:
        style_mod = 'digital' if ex_idx == 3 else 'photo'
    if num == 17 and stage == 1:
        cloth = [2,2,2,4,0][ex_idx]
    if num == 18 and stage == 1:
        cloth = [4,2,4,1,2][ex_idx]
        accessory = 'watch' if ex_idx == 2 else None
    if num == 19 and stage == 1:
        style_mod = ['digital', 'comic', 'anime', 'clay', 'digital'][ex_idx]
    if num == 20 and stage == 1:
        style_mod = ['old', 'water', 'bw', 'digital', 'digital'][ex_idx]
    if num == 21 and stage == 1:
        cloth = [1,1,4,2][ex_idx]
    if num == 23 and stage == 1 and ex_idx == 3:
        style_mod = 'bw'
    if num == 25:
        style_mod = 'old' if stage == 0 and ex_idx < 4 else ('bw' if ex_idx == 4 else 'photo')
    if num == 26 and stage == 1:
        pose = ex_idx
    if num == 27 and stage == 1:
        cloth = 2 if ex_idx < 3 else 1
    if num == 28 and stage == 1:
        cloth = [4,2,2,0,1][ex_idx]
    if num == 29 and stage == 1:
        cloth = [0,1,4,4,2][ex_idx]
        hair = 1 if ex_idx == 1 else hair
        angle = 1 if ex_idx == 1 else angle
    if num == 30 and stage == 1:
        cloth = [2,0,4,1,1,2][ex_idx]
        style_mod = ['photo', 'photo', 'photo', 'photo', 'digital', 'photo'][ex_idx]
        angle = 1 if ex_idx == 5 else angle

    parts = [draw_scene(num, ex_idx, stage, x, y, w, h, a1, a2)]
    parts.append(grade_overlay(num, ex_idx, stage, x, y, w, h))

    if stage == 0 and num in (1, 3, 9, 10, 12, 24, 25):
        issue_fill = ['#00000044', '#ff6b6b26', '#ffffff18', '#00000018', '#c59eff20', '#f6d06b22']
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{issue_fill[ex_idx % len(issue_fill)]}"/>')
    if stage == 1 and num == 2:
        lights = [
            f'<path d="M {x+10} {y+8} L {x+w*0.55:.1f} {y+h*0.2:.1f} L {x+w*0.4:.1f} {y+h} L {x} {y+h} Z" fill="#f6d06b" opacity="0.18"/>',
            f'<circle cx="{x+w*0.52:.1f}" cy="{y+h*0.18:.1f}" r="{h*0.3:.1f}" fill="#ffffff" opacity="0.18"/>',
            f'<circle cx="{x+w*0.5:.1f}" cy="{y+h*0.08:.1f}" r="{h*0.22:.1f}" fill="#fff3c6" opacity="0.2"/>',
            f'<path d="M {x+w*0.18:.1f} {y+h*0.2:.1f} Q {x+w*0.07:.1f} {y+h*0.52:.1f} {x+w*0.17:.1f} {y+h*0.84:.1f}" stroke="#ffffff" stroke-width="8" opacity="0.22" fill="none"/><path d="M {x+w*0.82:.1f} {y+h*0.2:.1f} Q {x+w*0.93:.1f} {y+h*0.52:.1f} {x+w*0.83:.1f} {y+h*0.84:.1f}" stroke="#ffffff" stroke-width="8" opacity="0.22" fill="none"/>',
            f'<path d="M {x+w*0.7:.1f} {y} L {x+w:.1f} {y} L {x+w:.1f} {y+h:.1f} L {x+w*0.58:.1f} {y+h:.1f} Z" fill="#f6d06b" opacity="0.16"/>',
        ]
        parts.append(lights[ex_idx])
    if stage == 1 and num == 5:
        lens_text = ['24', '35', '50', '85', '135'][ex_idx]
        rings = [28, 20, 12, 8, 5]
        for i in range(1, 4):
            r = rings[ex_idx] * i
            parts.append(f'<ellipse cx="{x+w*0.5:.1f}" cy="{y+h*0.48:.1f}" rx="{r*1.5:.1f}" ry="{r:.1f}" fill="none" stroke="#dff7ff" stroke-opacity="0.08"/>')
        parts.append(f'<text x="{x+w-12:.1f}" y="{y+18:.1f}" text-anchor="end" fill="#dff7ff" font-family="DejaVu Sans" font-size="13" font-weight="bold">{lens_text}mm</text>')
    if stage == 1 and num == 9:
        parts.append(f'<circle cx="{x+w*0.5:.1f}" cy="{y+h*0.38:.1f}" r="{h*0.2:.1f}" fill="#ffffff" opacity="0.07"/>')
    if stage == 0 and num == 9:
        dots = [(0.46,0.42),(0.51,0.44),(0.55,0.47),(0.48,0.5),(0.53,0.54)]
        color = ['#b55252', '#9d6a47', '#d26161', '#ce8e6a', '#ad604d'][ex_idx]
        for dx,dy in dots:
            parts.append(f'<circle cx="{x+w*dx:.1f}" cy="{y+h*dy:.1f}" r="2.4" fill="{color}" opacity="0.7"/>')
    if num == 10:
        if stage == 1 and ex_idx == 0:
            parts.append(f'<line x1="{x+w*0.44:.1f}" y1="{y+h*0.36:.1f}" x2="{x+w*0.47:.1f}" y2="{y+h*0.35:.1f}" stroke="#f6d06b"/><line x1="{x+w*0.54:.1f}" y1="{y+h*0.35:.1f}" x2="{x+w*0.57:.1f}" y2="{y+h*0.36:.1f}" stroke="#f6d06b"/>')
        if stage == 1 and ex_idx == 1:
            parts.append(f'<circle cx="{x+w*0.44:.1f}" cy="{y+h*0.41:.1f}" r="6" fill="#ffffff" opacity="0.10"/><circle cx="{x+w*0.56:.1f}" cy="{y+h*0.41:.1f}" r="6" fill="#ffffff" opacity="0.10"/>')
        if stage == 1 and ex_idx == 2:
            parts.append(f'<path d="M {x+w*0.4:.1f} {y+h*0.48:.1f} Q {x+w*0.5:.1f} {y+h*0.62:.1f} {x+w*0.6:.1f} {y+h*0.48:.1f}" stroke="#ffffff" stroke-opacity="0.18" fill="none"/>')
    if num == 12 and stage == 0:
        shapes = [
            f'<circle cx="{x+w*0.82:.1f}" cy="{y+h*0.55:.1f}" r="12" fill="#9ad8ff" opacity="0.7"/>',
            f'<path d="M {x+w*0.16:.1f} {y+10:.1f} L {x+w*0.2:.1f} {y+h-12:.1f}" stroke="#5f6f79" stroke-width="3"/>',
            f'<rect x="{x+w*0.72:.1f}" y="{y+h*0.32:.1f}" width="24" height="16" rx="3" fill="#f6d06b" opacity="0.8"/>',
            f'<rect x="{x+w*0.68:.1f}" y="{y+h*0.7:.1f}" width="24" height="18" rx="3" fill="#c39bff" opacity="0.8"/>',
            f'<polygon points="{x+w*0.78:.1f},{y+h*0.24:.1f} {x+w*0.9:.1f},{y+h*0.36:.1f} {x+w*0.84:.1f},{y+h*0.44:.1f}" fill="#66e6bf" opacity="0.7"/>'
        ]
        parts.append(shapes[ex_idx])
    if num == 13 and stage == 1:
        objs = [
            f'<rect x="{x+w*0.66:.1f}" y="{y+h*0.68:.1f}" width="28" height="18" rx="2" fill="#a7b6c7"/><path d="M {x+w*0.66:.1f} {y+h*0.86:.1f} h 28" stroke="#a7b6c7"/>',
            f'<rect x="{x+w*0.73:.1f}" y="{y+h*0.64:.1f}" width="12" height="24" rx="3" fill="#cfd3dd"/>',
            f'<rect x="{x+w*0.73:.1f}" y="{y+h*0.67:.1f}" width="14" height="18" rx="4" fill="#7c4b2c"/><ellipse cx="{x+w*0.74:.1f}" cy="{y+h*0.66:.1f}" rx="10" ry="3" fill="#faf2e8"/>',
            f'<rect x="{x+w*0.73:.1f}" y="{y+h*0.58:.1f}" width="16" height="12" rx="2" fill="#0b1018"/><circle cx="{x+w*0.74:.1f}" cy="{y+h*0.64:.1f}" r="6" fill="#1a2433" stroke="#9ad8ff" stroke-width="1"/>',
            f'<rect x="{x+w*0.72:.1f}" y="{y+h*0.66:.1f}" width="20" height="16" rx="2" fill="#7a6040"/>',
            f'<rect x="{x+w*0.82:.1f}" y="{y+h*0.46:.1f}" width="10" height="30" fill="#5a7956"/><circle cx="{x+w*0.825:.1f}" cy="{y+h*0.44:.1f}" r="10" fill="#72b574"/>'
        ]
        parts.append(objs[ex_idx])
    if stage == 1 and num == 18 and ex_idx in (1,2):
        parts.append(f'<circle cx="{x+w*0.78:.1f}" cy="{y+h*0.36:.1f}" r="16" fill="{a1}" opacity="0.18"/>')
    if stage == 1 and num == 24:
        for i in range(3):
            parts.append(f'<rect x="{x+12+i*8}" y="{y+12+i*8}" width="{w-24-i*16}" height="{h-24-i*16}" rx="14" fill="none" stroke="#ffffff" stroke-opacity="0.06"/>')
    if stage == 0 and num == 24:
        if ex_idx in (0,2):
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" opacity="0.05"/>')
        if ex_idx == 3:
            for i in range(18):
                parts.append(f'<circle cx="{x+8+(i*13%int(w-16))}" cy="{y+8+(i*17%int(h-16))}" r="1.2" fill="#ffffff" opacity="0.25"/>')
    if stage == 1 and num == 28:
        ui = [
            f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="12" fill="none" stroke="#ff7eb9" stroke-opacity="0.35"/>',
            f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="12" fill="none" stroke="#7fb7ff" stroke-opacity="0.35"/>',
            f'<path d="M {x+14} {y+18} H {x+w-14}" stroke="#f6d06b" stroke-opacity="0.35"/>',
            f'<circle cx="{x+w*0.82:.1f}" cy="{y+26:.1f}" r="10" fill="#dce5ea" opacity="0.25"/>',
            f'<rect x="{x+12}" y="{y+h*0.76:.1f}" width="{w-24}" height="14" rx="7" fill="#ffffff" opacity="0.08"/>'
        ]
        parts.append(ui[ex_idx])

    sx, sy, sw, sh = x + w*0.18, y + h*0.12, w*0.64, h*0.76
    parts.append(f'<g transform="translate({sx:.1f},{sy:.1f}) scale({sw/100:.3f},{sh/120:.3f})">{subject_parts(style_mod, hair, expr, cloth, accessory, pose, angle)}</g>')
    return ''.join(parts)


def card(x, y, w, h, name, prompt, story, ex_idx, a1, a2, a3, compact=False, wide=False):
    pad = 18
    small = h <= 260
    title_size = 22 if compact else 26
    prompt_size = 14 if compact else 16
    prompt_width = 37 if wide else (31 if compact else 34)
    visual_h = 126 if compact else 140

    if small:
        title_size = 18
        prompt_size = 12.5
        prompt_width = 32
        visual_h = 96
    if len(prompt) > 150:
        prompt_size = min(prompt_size, 13)
        prompt_width += 7
        visual_h -= 10
    if small and len(prompt) > 190:
        title_size = 17
        prompt_size = 11.5
        prompt_width = 52
        visual_h = 78

    if wide:
        visual_w = 332
        visual_h = h - 40
        px = x + 18
        py = y + 20
        title_lines = wrap(name, 24)
        parts = [f'<g filter="url(#shadow)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="url(#glass)" stroke="{a1}" stroke-opacity="0.35"/></g>']
        parts.append(text_block(x + w - 22, y + 38, title_lines, 24, 'white', anchor='end', weight='bold'))
        parts.append(f'<g><rect x="{px}" y="{py}" width="{visual_w/2-6:.1f}" height="{visual_h}" rx="18" fill="#0c1916"/><rect x="{px+visual_w/2+6:.1f}" y="{py}" width="{visual_w/2-6:.1f}" height="{visual_h}" rx="18" fill="#0c1916"/>{preview(story, ex_idx, 0, px, py, visual_w/2-6, visual_h, a1, a2, a3)}{preview(story, ex_idx, 1, px+visual_w/2+6, py, visual_w/2-6, visual_h, a1, a2, a3)}</g>')
        parts.append(f'<text x="{px+16}" y="{py+19}" fill="#d8e6e1" font-family="DejaVu Sans" font-size="13" font-weight="bold">BEFORE</text>')
        parts.append(f'<text x="{px+visual_w/2+24}" y="{py+19}" fill="{a1}" font-family="DejaVu Sans" font-size="13" font-weight="bold">AFTER</text>')
        title_h = 24 + (len(title_lines)-1) * 28
        parts.append(text_block(x + 382, y + 34 + title_h, wrap(prompt, 46), 16, '#cfe3dd', family='DejaVu Sans'))
        return ''.join(parts)

    parts = [f'<g filter="url(#shadow)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="url(#glass)" stroke="{a1}" stroke-opacity="0.35"/></g>']
    parts.append(text_block(x + 20, y + 34, wrap(name, 17 if not small else 15), title_size, 'white', weight='bold'))
    px = x + pad
    py = y + (46 if small else 50)
    pw = (w - pad*2 - 12) / 2
    ph = visual_h
    parts.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="18" fill="#0c1916"/><rect x="{px+pw+12}" y="{py}" width="{pw}" height="{ph}" rx="18" fill="#0c1916"/>')
    parts.append(preview(story, ex_idx, 0, px, py, pw, ph, a1, a2, a3))
    parts.append(preview(story, ex_idx, 1, px + pw + 12, py, pw, ph, a1, a2, a3))
    parts.append(f'<text x="{px+16}" y="{py+19}" fill="#d8e6e1" font-family="DejaVu Sans" font-size="13" font-weight="bold">BEFORE</text>')
    parts.append(f'<text x="{px+pw+28}" y="{py+19}" fill="{a1}" font-family="DejaVu Sans" font-size="13" font-weight="bold">AFTER</text>')
    prompt_y = py + ph + (24 if small else 28)
    parts.append(text_block(x + 20, prompt_y, wrap(prompt, prompt_width), prompt_size, '#cfe3dd', family='DejaVu Sans'))
    return ''.join(parts)


def positions(layout):
    if layout == 'grid4':
        return [(55, 430, 470, 408), (555, 430, 470, 408), (55, 872, 470, 408), (555, 872, 470, 408)]
    if layout == 'grid6':
        return [(55, 408, 470, 310), (555, 408, 470, 310), (55, 736, 470, 310), (555, 736, 470, 310), (55, 1064, 470, 310), (555, 1064, 470, 310)]
    if layout == 'timeline5':
        return [(85, 430, 910, 188), (85, 640, 910, 188), (85, 850, 910, 188), (85, 1060, 910, 188), (85, 1270, 910, 188)]
    if layout == 'editorial5':
        return [(55, 410, 470, 450), (555, 410, 470, 235), (555, 670, 470, 235), (55, 930, 470, 235), (555, 930, 470, 235)]
    if layout == 'process6':
        return [(55, 700, 470, 238), (555, 700, 470, 238), (55, 970, 470, 238), (555, 970, 470, 238), (55, 1240, 470, 238), (555, 1240, 470, 238)]
    return [(55, 410, 470, 300), (555, 410, 470, 300), (55, 740, 470, 300), (555, 740, 470, 300), (55, 1070, 970, 300)]


def process_band(a1, a2):
    boxes = [
        (55, 400, 290, 220, 'Original', '#11231f'),
        (395, 400, 290, 220, 'AI Editing Process', '#172520'),
        (735, 400, 290, 220, 'Final Result', '#1a2923'),
    ]
    parts = []
    for x, y, w, h, label, fill in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="{fill}" stroke="{a1}" stroke-opacity="0.35"/>')
        parts.append(f'<text x="{x+w/2:.1f}" y="{y+38}" text-anchor="middle" fill="#f6d06b" font-family="DejaVu Sans" font-size="22" font-weight="bold">{label}</text>')
    parts.append(draw_scene(30, 0, 0, 95, 452, 210, 102, a1, a2))
    parts.append(f'<g transform="translate(127,453) scale(1.55,0.85)">{subject_parts()}</g>')
    parts.append(text_block(200, 594, ['پرتره مرجع'], 18, '#d8e6e1', anchor='middle', weight='bold'))
    parts.append(text_block(540, 505, ['سوژه → لباس → ژست', 'محیط → نور → رنگ → هویت'], 18, '#d8e6e1', anchor='middle'))
    parts.append(text_block(540, 568, ['ویرایش کنترل‌شده و', 'مرحله‌به‌مرحله'], 18, '#ffffff', anchor='middle', weight='bold'))
    parts.append(draw_scene(30, 5, 1, 775, 452, 210, 102, a1, a2))
    parts.append(f'<g transform="translate(807,453) scale(1.55,0.85)">{subject_parts(cloth=2, angle=1)}</g>')
    parts.append(text_block(880, 588, ['خروجی نهایی', 'لوکس، کنترل‌شده، قابل‌تکرار'], 17, '#ffffff', anchor='middle', weight='bold'))
    parts.append(f'<path d="M 346 510 H 385" stroke="{a2}" stroke-width="4" stroke-linecap="round"/><path d="M 686 510 H 725" stroke="{a2}" stroke-width="4" stroke-linecap="round"/>')
    return ''.join(parts)


def title_metrics(story):
    title = f"{story['num']:02d} | {story['title']}"
    size = 60 if len(title) <= 18 else 54 if len(title) <= 24 else 48
    width = 22 if len(title) <= 22 else 18
    lines = wrap(title, width)
    if len(lines) > 1:
        size -= 2
    subtitle = story['subtitle']
    sub_size = 28 if len(subtitle) <= 34 else 26
    sub_lines = wrap(subtitle, 38 if len(subtitle) <= 42 else 32)
    title_y = 280 if len(lines) == 1 else 256
    title_h = size + (len(lines)-1) * size * 1.25
    subtitle_y = title_y + title_h + 18
    subtitle_h = sub_size + (len(sub_lines)-1) * sub_size * 1.35
    badge_y = subtitle_y + subtitle_h + 16
    return title, lines, size, subtitle, sub_lines, sub_size, title_y, subtitle_y, badge_y


def render_story(story):
    a1, a2, a3 = PALETTES[story['palette']]
    num = story['num']
    title, title_lines, title_size, subtitle, subtitle_lines, subtitle_size, title_y, subtitle_y, badge_y = title_metrics(story)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(svg_defs(a1, a2, a3))
    parts.append('<rect width="1080" height="1920" fill="url(#bg)"/>')
    parts.append('<rect width="1080" height="1920" fill="url(#glowA)"/><rect width="1080" height="1920" fill="url(#glowB)"/>')
    for gx in range(0, 1081, 108):
        parts.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="1920" stroke="#ffffff" stroke-opacity="0.03"/>')
    for gy in range(0, 1921, 160):
        parts.append(f'<line x1="0" y1="{gy}" x2="1080" y2="{gy}" stroke="#ffffff" stroke-opacity="0.02"/>')

    parts.append(chips(story, a1))
    parts.append(text_block(540, title_y, title_lines, title_size, 'white', anchor='middle', weight='bold'))
    parts.append(text_block(540, subtitle_y, subtitle_lines, subtitle_size, '#d2e1dd', anchor='middle'))
    parts.append(f'<rect x="322" y="{badge_y:.1f}" width="436" height="40" rx="20" fill="#0d1d1a" stroke="{a2}" stroke-opacity="0.4"/>'
                 f'<text x="540" y="{badge_y+26:.1f}" text-anchor="middle" fill="{a1}" font-family="DejaVu Sans" font-size="20" font-weight="bold">Identity Lock • Prompt Match • Same Subject</text>')

    if story['layout'] == 'process6':
        parts.append(process_band(a1, a2))

    pos = positions(story['layout'])
    for i, (name, prompt) in enumerate(story['examples']):
        x, y, w, h = pos[i]
        parts.append(card(x, y, w, h, name, prompt, story, i, a1, a2, a3, compact=(story['layout'] in ('grid6', 'process6')), wide=(story['layout']=='timeline5')))

    tip_lines = wrap(story['tip'], 52)
    tip_size = 22 if max(len(line) for line in tip_lines) < 36 else 20
    parts.append(f'<rect x="70" y="1510" width="940" height="126" rx="32" fill="#10241f" stroke="url(#gold)" stroke-width="2.5"/>')
    parts.append('<text x="540" y="1544" text-anchor="middle" fill="#f6d06b" font-family="DejaVu Sans" font-size="20" font-weight="bold">نکته حرفه‌ای</text>')
    parts.append(text_block(540, 1580, tip_lines, tip_size, '#f4ead2', anchor='middle', weight='bold'))

    cta1 = 'Save this Prompt'
    cta2 = 'این Prompt را ذخیره کن'
    if num == 30:
        cta1 = 'AI Editing'
        cta2 = '۳۰ تکنیک یاد گرفتی؛ حالا پرامپت خودت را بساز.'
    parts.append(f'<rect x="140" y="1672" width="800" height="82" rx="28" fill="#08110f" stroke="{a1}" stroke-width="2"/>'
                 f'<text x="540" y="1706" text-anchor="middle" fill="#ffffff" font-family="DejaVu Sans" font-size="32" font-weight="bold">{cta1}</text>'
                 f'<text x="540" y="1736" text-anchor="middle" fill="{a1}" font-family="DejaVu Sans" font-size="22">{cta2}</text>')
    if num == 30:
        parts.append('<text x="540" y="1800" text-anchor="middle" fill="#f6d06b" font-family="DejaVu Sans" font-size="36" font-weight="bold">تغییر کنترل‌شده؛ نه تغییر هویت.</text>')
    else:
        parts.append('<text x="540" y="1800" text-anchor="middle" fill="#f6d06b" font-family="DejaVu Sans" font-size="34" font-weight="bold">SUN • AI Image Editing Course</text>')
    parts.append('<text x="540" y="1838" text-anchor="middle" fill="#8aa099" font-family="DejaVu Sans" font-size="19">Premium Prompting • Before / After • Identity-Safe Editing</text>')
    parts.append('</svg>')
    svg = ''.join(parts)
    (OUT / f'{story["slug"]}.svg').write_text(svg, encoding='utf-8')

    md = [
        f'# Story {num:02d} — {story["title"]}',
        '',
        f'![{story["slug"]}](./{story["slug"]}.png)',
        '',
        f'**موضوع:** {story["subtitle"]}',
        '',
        '## زمان انتشار',
        '- Instagram: `h.alavian`',
        '- نوع: `Story`',
        '- زمان: `2026-09-17 00:00` به وقت ایران (Asia/Tehran)',
        '- انتشار خودکار: فعال',
        '- محتوای تولید/ویرایش‌شده با AI: بله',
        '',
        '## قانون ثابت هویت چهره',
        f'> {IDENTITY_ANCHOR}',
        '',
        '## پرامپت‌های استفاده‌شده در استوری',
    ]
    for i, (name, prompt) in enumerate(story['examples'], 1):
        md.append(f'{i}. **{name}:** `{prompt}`')
    md.extend(['', f'> نکته: {story["tip"]}', ''])
    (OUT / f'{story["slug"]}.md').write_text('\n'.join(md), encoding='utf-8')


def write_index():
    lines = [
        '# AI Image Editing Course — 30 Instagram Stories',
        '',
        'این پوشه شامل ۳۰ استوری مستقل 1080×1920 برای آموزش AI Image Editing است.',
        '',
        '## ساختار',
        '- هر استوری: فایل SVG + فایل MD + PNG رندرشده',
        '- طراحی: Premium / Futuristic / AI Education / Cinematic',
        '- زبان آموزشی: فارسی',
        '- Promptها: انگلیسی و کپی‌پذیر',
        '',
        '## فهرست استوری‌ها',
    ]
    for story in STORIES:
        lines.append(f'- `{story["slug"]}` — {story["title"]}')
    lines.extend(['', '## قانون ثابت هویت چهره', f'> {IDENTITY_ANCHOR}', ''])
    (OUT / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


for story in STORIES:
    render_story(story)
write_index()
print(f'Generated {len(STORIES)} SVG + MD pairs in {OUT}')
