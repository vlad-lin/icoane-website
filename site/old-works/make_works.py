"""Writes works.json: the icons from the 2019-2020 archive ("poze vechi", not published).

The archive itself stays on this PC only; this file records what the site takes from it:
which photo, how it is cropped, and the facts and description she wrote in 2019.
Edit this script (or works.json directly) and run the full chain in site/README.md.
"""
import json
import os

TECH = ('Pictată manual pe sticlă, în tempera și foiță de aur, pe un desen realizat cu penița și tușul '
        'după izvod original. Rama, din lemn de brad băițuit, este lucrată tot manual.')

PARASCHEVA = ('Tema acestei icoane este Sfânta Cuvioasă Parascheva cea Nouă, sau Parascheva de la Iași, o sfântă '
              'cinstită în întreaga Biserică Ortodoxă, îndeosebi în România, Serbia, Grecia și Bulgaria. În România '
              'este considerată ocrotitoarea Moldovei și este cea mai populară dintre toți sfinții ale căror moaște '
              'se află pe teritoriul țării. Sute de biserici de parohie îi sunt închinate. În popor mai este cunoscută '
              'și ca Sfânta Vineri. Prăznuirea ei se face la 14 octombrie, când zeci de mii de oameni vin în fiecare '
              'an la Iași pentru a se închina la sfintele sale moaște.')
ADAM = ('Adam și Eva au fost, după Cartea Facerii (prima carte a Vechiului Testament și a Bibliei), primul bărbat '
        'și prima femeie create de Dumnezeu. Momentul în care cei doi încalcă porunca divină și gustă din Pomul '
        'Cunoașterii este o temă frecventă în iconografie. Această temă i-a atras și pe iconarii transilvăneni, '
        'care au pictat pe sticlă faimoasa scenă din Vechiul Testament.')
PETRU = ('În iconografia ortodoxă, Sfinții Petru și Pavel (primul și ultimul între Apostoli) reprezintă Biserica, '
         'sau comuniunea lui Israel (Petru) cu toate popoarele lumii (Pavel). Modelul Bisericii susținut de cei doi '
         'sfinți ilustrează cuvintele lui Iisus: „Tu ești Petru și pe această piatră voi construi Biserica Mea”.')
VITA = ('Iisus – Vița de vie este o temă care se regăsește în icoanele țărănești transilvănene, evocând taina '
        'Sfintei Împărtășanii. Icoana ilustrează pilda viței de vie: „Eu sunt vița, voi sunteți mlădițele”. Iisus '
        'S-a înfățișat pe Sine ca vița cea adevărată, pe Tatăl Său ca viticultorul care a sădit-o, iar pe ucenicii '
        'Săi ca mlădițele acestei vițe. Este vorba despre un arhetip potrivit căruia din jertfa primordială au '
        'crescut elementele esențiale ale vieții: hrana, vindecarea și cultul.')


def T(*paras):
    return '\n\n'.join(paras)


S = 'sorted/'
# date: the day the photo was taken (camera data or the WhatsApp file name).
# date_approx: no date known; shown as "before 2020" (the portfolio document is from August 2019).
# crop: [left, top, width, height] as fractions of the (upright) photo; omitted = whole photo.
WORKS = [
    dict(id='v1', date='2019-08-09', title='Nașterea Domnului', theme='praznice',
         izvod='Nicula, sfârșitul sec. XVIII', dimensiuni='21 × 29 cm', sarbatoare='25 decembrie',
         photo=S + '_001 Nasterea lui Iisus/icoana_05_canon-0001 (1).jpg',
         text=T('Tema acestei icoane (Nicula, sfârșitul secolului al XVIII-lea) este Nașterea Domnului.',
                'La 25 decembrie creștinii din întreaga lume celebrează Crăciunul – Sărbătoarea Nașterii Domnului. '
                'Acum mai bine de două mii de ani, Fecioara Maria (prin puterea Duhului Sfânt) a născut în Betleemul '
                'Iudeii, într-o iesle săracă, pe Pruncul Iisus. Atunci, cei trei magi de la Răsărit au văzut o stea '
                'luminoasă pe cer și, străbătând cale lungă pentru a o urma, au ajuns la Betleem, aducându-I '
                'Mântuitorului în dar aur, smirnă și tămâie. Crăciunul, în accepțiunea de astăzi, datează din anul '
                '325; până atunci, religiile precreștine marcau în aceeași perioadă a anului solstițiul de iarnă.',
                TECH)),
    dict(id='v2', date='2019-08-09', title='Sfântul Proroc Ilie', theme='sfinti',
         dimensiuni='11 × 14 cm', sarbatoare='20 iulie',
         photo=S + '_002 Sfantul Ilie/icoana_04_canon-0003_flash-2.jpg',
         text=T('La 20 iulie Biserica Ortodoxă Română sărbătorește ridicarea la cer a Sfântului Mare Proroc Ilie '
                'Tesviteanul (era de origine din Tesvi). Unul dintre cei mai importanți proroci din Vechiul '
                'Testament, Sfântul Ilie este celebrat ca un mare făcător de minuni și aducător de ploi în vreme de '
                'secetă.',
                'Reprezentat iconografic fie în gura peșterii sale, hrănit de corb, fie în carul de foc în care a '
                'fost răpit la cer, Sfântul Mare Proroc Ilie este, în calendarul bisericesc și în tradiția populară, '
                'personajul din Vechiul Testament cel mai familiar conștiinței creștine, iar Noul Testament sugerează '
                'că el va fi Înaintemergătorul celei de a doua veniri a lui Iisus.',
                TECH)),
    dict(id='v3', date='2019-08-09', title='Sfânta Cuvioasă Parascheva', theme='sfinti',
         izvod='Nicula, sec. XIX', dimensiuni='21 × 29 cm', sarbatoare='14 octombrie',
         photo=S + '_003 Sfanta Parascheva/icoana_06_telefon-0001-2.jpg',
         text=T(PARASCHEVA, TECH)),
    dict(id='v4', date='2019-08-09', title='Sfântul Ierarh Nicolae', theme='sfinti',
         izvod='Cârțișoara, 1894', dimensiuni='21 × 29 cm', sarbatoare='6 decembrie',
         photo=S + '_004 Sfantul Nicolae/icoana_07_telefon-0002-2.jpg',
         text=T('În fiecare an, pe 6 decembrie, credincioșii îl sărbătoresc pe unul dintre cei mai iubiți sfinți, '
                'Sfântul Nicolae. Este numit și „făcătorul de minuni” pentru mulțimea minunilor săvârșite încă din '
                'timpul vieții. Despre Sfântul Nicolae există numeroase legende, iar de ziua lui sunt legate mai '
                'multe obiceiuri și tradiții. Cel mai cunoscut rămâne cel al oferirii de daruri: copiii (dar și '
                'adulții, de ce nu?) își așază încă din ajunul sărbătorii, pe 5 decembrie, ghetuțele la geam sau la '
                'ușă, iar Moș Nicolae le pune în ele daruri. Celor mai năstrușnici le aduce însă câte o nuielușă.',
                TECH)),
    dict(id='v5', date='2019-08-09', title='Buna Vestire', theme='maica',
         izvod='Nicula, mijlocul secolului XIX', dimensiuni='21 × 29 cm', sarbatoare='25 martie',
         photo=S + '_007 Buna Vestire/icoana_08_canon-0004_flash-2.jpg',
         text=T('Tema acestei icoane este Buna Vestire, sărbătorită de Biserica Ortodoxă în fiecare an pe 25 martie: '
                'ziua în care Sfântul Arhanghel Gavriil aduce pe Pământ vestea Nașterii Fiului lui Dumnezeu. El '
                'poposește într-o cetate din Galileea, numită Nazaret, la o fecioară logodită cu un bărbat pe nume '
                'Iosif, și o vestește că va naște pe Mesia. Numele fecioarei era Maria – Sfânta Fecioară Maria. '
                'Vestea cea bună dată neamului omenesc despre întruparea Fiului lui Dumnezeu completează, de fapt, '
                'sărbătoarea noastră personală, adică propria noastră bunăvestire.',
                TECH)),
    dict(id='v6', date='2019-08-09', title='Masa Raiului', theme='masa',
         izvod='Nicula, prima jumătate a sec. XIX', dimensiuni='21 × 29 cm',
         photo=S + '_008 Masa Raiului/icoana_11_canon-0002.jpg', crop=[0.37, 0.05, 0.56, 0.76],
         text=T('Caracteristică zonei Nicula este icoana „Mesei Raiului”, înfățișând o masă în formă de romb în care '
                'sunt reprezentați Fecioara Maria, Mântuitorul Iisus Hristos și doi sfinți. În această icoană (după un '
                'izvod din prima jumătate a secolului al XIX-lea), cei doi sfinți sunt Sfântul Nicolae și Sfânta '
                'Parascheva.',
                TECH)),
    dict(id='v7', date='2019-08-09', title='Sfinții Împărați Constantin și Elena', theme='sfinti',
         izvod='Nicula, mijlocul secolului XIX', dimensiuni='21 × 29 cm', sarbatoare='21 mai',
         photo=S + '_009 Sfintii Constantin si Elena/icoana_13_canon-0002.jpg', crop=[0.37, 0.03, 0.57, 0.76],
         text=T('Tema acestei icoane îi reprezintă pe Sfinții Împărați Constantin și Elena.',
                'Gaius Flavius Valerius Aurelius Constantinus (n. 272/274 – d. mai 337), cunoscut și ca Constantin I '
                'sau Constantin cel Mare, a fost împărat roman între 306 și 337, devenind conducătorul întregului '
                'Imperiu Roman după înfrângerea lui Maxențiu și a lui Liciniu. Flavia Iulia Helena (248–329), soția '
                'generalului roman Constantius Chlorus, a fost mama Sfântului Împărat Constantin cel Mare. A fost o '
                'femeie deosebit de credincioasă, cunoscută pentru evlavia ei. A făcut pelerinaj în Palestina și în '
                'provinciile răsăritene, iar tradiția îi atribuie găsirea Sfintei Cruci a lui Hristos și aflarea '
                'rămășițelor celor trei magi.',
                'Sărbătoarea Sfinților Constantin și Elena este una dintre cele mai însemnate pentru creștini, '
                'întrucât împăratul Constantin i-a eliberat de sub prigoana păgână (prin Edictul de la Mediolanum, din '
                '313), iar toată activitatea sa, sub sfatul mamei sale, Elena, a fost una de ocrotire a noii religii.',
                TECH)),
    dict(id='v8', date='2019-08-09', title='Maica Domnului cu Pruncul', theme='maica',
         izvod='Transilvania de Nord, mijlocul sec. XIX', dimensiuni='15 × 21 cm',
         photo=S + '_010 Fecioara cu Pruncul/icoana_03_canon-0002_flash.jpg', crop=[0.32, 0.15, 0.63, 0.80],
         text=T('Specialiștii afirmă că această icoană pictată pe sticlă (a cărei proveniență ar fi mijlocul '
                'secolului al XIX-lea, nordul Transilvaniei) este o combinație de elemente ortodoxe și catolice.',
                'Iconarii din toate timpurile au încercat să o înfățișeze pe Maica Domnului cât mai frumoasă, blândă, '
                'demnă și slăvită. Uneori au pictat-o mâhnită, alteori îndurerată, dar întotdeauna plină de tărie '
                'spirituală și de înțelepciune. Preacurata este înfățișată întotdeauna cu capul acoperit de o '
                'năframă care îi cade pe umeri, după tradiția iudaică a acelor vremuri. În cele mai multe icoane, '
                'Maica Domnului ține Pruncul pe mâna stângă și arată spre El cu mâna dreaptă; această icoană, pictată '
                'pe sticlă antireflex, este una dintre variantele în care Pruncul este ținut în mâna dreaptă.',
                TECH)),
    dict(id='v9', date='2019-08-09', title='Maica Domnului Împărățită', theme='maica',
         izvod='Șcheii Brașovului, 1780', dimensiuni='21 × 29 cm',
         photo=S + '_011 Maica Domnului Imparatita/Export/icoana_15_telefon-0002.jpg',
         text=T('Icoana Maicii Domnului (Șcheii Brașovului, 1780) o reprezintă pe prima ființă umană care a împlinit '
                'scopul Întrupării: îndumnezeirea omului. Este una dintre imaginile cu coroană ale Împărătesei '
                'îngerilor, cu Pruncul Sfânt la piept și îngerii așezându-i coroana pe cap.',
                TECH)),
    dict(id='v10', date='2019-08-09', title='Sfinții Arhangheli Mihail și Gavriil', theme='sfinti',
         izvod='Maierii (Alba Iulia), prima jumătate a sec. XIX', dimensiuni='21 × 29 cm', sarbatoare='8 noiembrie',
         photo=S + '_012 Mihail si Gavril/Export/icoana_14_telefon-0002-2.jpg', crop=[0.30, 0.04, 0.56, 0.72],
         text=T('Tema acestei icoane este Sărbătoarea Sfinților Arhangheli Mihail („puterea lui Dumnezeu”) și '
                'Gavriil („bărbat-Dumnezeu”), fixată în calendarul bizantin pe 8 noiembrie, iar în cel latin pe 29 '
                'septembrie. Acești sfinți sunt patronii multor biserici, fiind cunoscuți drept conducătorii cetelor '
                'de îngeri, păzitorii oamenilor de la naștere până la moarte și călăuzele sufletelor în drumul lor '
                'spre Rai.',
                TECH)),
    dict(id='v11', date='2019-12-09', title='Sfânta Cuvioasă Parascheva', theme='sfinti',
         izvod='Nicula, prima jumătate a sec. XIX', dimensiuni='15 × 21 cm', sarbatoare='14 octombrie',
         photo=S + '_013 Sfanta Parascheva 2/Export/Sfanta Paraschevab.jpg', crop=[0.0, 0.0, 1.0, 0.72],
         text=T(PARASCHEVA, TECH)),
    dict(id='v12', date='2019-12-09', title='Sfântul Mare Mucenic Gheorghe', theme='sfinti',
         izvod='Nicula, începutul sec. XIX', dimensiuni='15 × 21 cm', sarbatoare='23 aprilie',
         photo=S + '_014 Sfantul Gheorghe/Export/Sf.Gheorghe.3.jpg', crop=[0.0, 0.06, 0.9, 0.73],
         text=T('Tema acestei icoane este Sfântul Mare Mucenic Gheorghe. A fost un soldat roman de origine greacă, '
                'ofițer în garda împăratului Dioclețian, condamnat la moarte pentru că nu a renunțat la credința '
                'creștină. Ca martir, a devenit mai târziu unul dintre cei mai venerați sfinți ai creștinătății. Este '
                'pomenit de aproape toate Bisericile tradiționale, de obicei pe 23 aprilie, și este socotit '
                'ocrotitorul multor țări, regiuni și orașe din întreaga lume.',
                TECH)),
    dict(id='v13', date='2019-12-09', title='Adam și Eva în Rai', theme='praznice',
         izvod='Nicula, a doua jumătate a sec. XIX', dimensiuni='15 × 21 cm',
         photo=S + '_015 Adam si Eva/Export/Adam si Eva 1.b.jpg', crop=[0.0, 0.01, 0.85, 0.75],
         text=T(ADAM, TECH)),
    dict(id='v14', date='2019-12-09', title='Sfinții Apostoli Petru și Pavel', theme='sfinti',
         izvod='Nicula, începutul sec. XIX', dimensiuni='15 × 21 cm', sarbatoare='29 iunie',
         photo=S + '_016 Sfintii Petru si Pavel/Export/Sfintii Petru si Pavel 3.jpg', crop=[0.0, 0.01, 1.0, 0.76],
         text=T(PETRU, TECH)),
    dict(id='v15', date='2019-12-11', title='Sfântul Ierarh Nicolae', theme='sfinti',
         izvod='Nicula, 1867', dimensiuni='17 × 25 cm', sarbatoare='6 decembrie',
         photo=S + '_017 Sfantul Nicolae 2/Export/Sfantul Nicolae.a2.jpg', crop=[0.0, 0.01, 1.0, 0.79],
         text=T('Tema acestei icoane (Nicula, 1867) este Sfântul Nicolae, sărbătorit atât de Biserica Ortodoxă, cât '
                'și de cea Romano-Catolică, pe 6 decembrie. Sfântul Nicolae este socotit ocrotitorul copiilor, mai '
                'ales al celor săraci, dar și al marinarilor, al brutarilor, al fetelor nemăritate și al celor '
                'acuzați pe nedrept. De la el a pornit tradiția oferirii de daruri.',
                'S-a născut în a doua jumătate a secolului al III-lea, într-o familie bogată, în localitatea Patara, '
                'în provincia Licia, în partea asiatică a Turciei de astăzi. Încă din tinerețe a avut o chemare spre '
                'viața duhovnicească. Rămas fără părinți, a folosit averea moștenită pentru a-i ajuta pe cei săraci '
                'și pentru a ridica o biserică. Moaștele Sfântului Nicolae sunt păstrate la Bari, în Italia, într-o '
                'criptă din care izvorăște un lichid incolor, numit „Mana”. Potrivit tradiției, episcopul locului '
                'amestecă acest lichid cu apă, îl binecuvântează și îl împarte credincioșilor.',
                TECH)),
    dict(id='v16', date='2019-12-11', title='Iisus Hristos – Vița de vie', theme='praznice',
         izvod='Nicula, începutul sec. XIX', dimensiuni='17 × 25 cm',
         photo=S + '_018 Iisus vita de vie 2/Export/Iisus -Vita de vie 3.jpg', crop=[0.06, 0.02, 0.88, 0.78],
         text=T(VITA, TECH)),
    dict(id='v17', date='2019-12-11', title='Iisus Hristos – Vița de vie', theme='praznice',
         izvod='Nicula, începutul sec. XIX', dimensiuni='17 × 25 cm',
         photo=S + '_019 Iisus vita de vie 1/Export/Iisus vita de vie 1.jpg', crop=[0.0, 0.0, 1.0, 0.72],
         text=T(VITA, TECH)),
    dict(id='v18', date='2019-12-09', title='Maica Domnului cu Pruncul', theme='maica',
         dimensiuni='17 × 25 cm',
         photo=S + '_020 Fecioara cu Pruncul/Export/Fecioara1a.jpg', crop=[0.0, 0.0, 1.0, 0.79],
         text=T('Modelul obișnuit al icoanei Fecioara cu Pruncul, întâlnit și în Răsărit, și în Apus, este Fecioara '
                'ținându-L pe Prunc. Ea cuprinde mai multe lucruri, nu doar pe Maica lui Dumnezeu ca persoană: este o '
                'imagine și o afirmare a întrupării și a realității ei, o afirmare a maternității adevărate și reale '
                'a Fecioarei.',
                'Dacă te uiți cu atenție la icoană, vei vedea că Maica lui Dumnezeu, ținându-L pe Prunc, nu privește '
                'niciodată la El. Nu privește nici la tine, nici în depărtare: ochii îi sunt întotdeauna ațintiți '
                'înlăuntrul ei, în contemplare. Tandrețea îi este exprimată de sfiiciunea mâinilor. Ea îl ține pe '
                'Prunc fără a-L îmbrățișa, așa cum cineva ar ține ceva sfânt pe care îl aduce ca ofrandă, iar toată '
                'tandrețea, toată iubirea omenească sunt exprimate de Prunc, nu de mamă. Ea rămâne Maica lui Dumnezeu '
                'și se poartă cu Pruncul nu ca și cum ar fi un copil oarecare, ci ca față de Fiul lui Dumnezeu '
                'întrupat, Care S-a făcut fiu al Fecioarei; iar El, fiind om adevărat și Dumnezeu adevărat, își arată '
                'față de ea toată iubirea și tandrețea omului și a lui Dumnezeu.',
                TECH)),
    # Only in the portfolio document (Portofoliu icoane.docx, August 2019): no photo date.
    dict(id='v19', date='2019-08-07', date_approx=True, title='Sfinții Apostoli Petru și Pavel', theme='sfinti',
         izvod='Nicula, începutul sec. XIX', sarbatoare='29 iunie',
         photo='Portofoliu icoane.docx#word/media/image4.jpeg', text=T(PETRU, TECH)),
    dict(id='v20', date='2019-08-07', date_approx=True, title='Iisus Hristos – Vița de vie', theme='praznice',
         izvod='Șcheii Brașovului, mijlocul sec. XIX',
         photo='Portofoliu icoane.docx#word/media/image6.jpeg', text=T(VITA, TECH)),
    dict(id='v21', date='2019-08-07', date_approx=True, title='Adam și Eva în Rai', theme='praznice',
         izvod='Nicula, a doua jumătate a sec. XIX',
         photo='Portofoliu icoane.docx#word/media/image8.jpeg', text=T(ADAM, TECH)),
    # 2020, from the unsorted photos (dates from the WhatsApp file names). No description was written.
    dict(id='v22', date='2020-05-16', title='Învierea Domnului', theme='praznice',
         photo='unsorted/IMG-20200516-WA0001.jpg', crop=[0.13, 0.0, 0.82, 0.93], text=''),
    dict(id='v23', date='2020-08-19', title='Înălțarea Sfintei Cruci', theme='praznice', sarbatoare='14 septembrie',
         photo='unsorted/IMG-20200819-WA0003.jpg', crop=[0.17, 0.05, 0.83, 0.89], text=''),
    dict(id='v24', date='2020-11-01', title='Iisus Hristos – Vița de vie', theme='praznice',
         photo='unsorted/IMG-20201101-WA0000.jpg', crop=[0.03, 0.0, 0.94, 0.79], text=''),
    dict(id='v25', date='2020-11-26', title='Sfântul Ciprian și Sfântul Ștefan', theme='sfinti',
         photo='unsorted/IMG-20201126-WA0000.jpg', crop=[0.0, 0.08, 1.0, 0.79], text=''),
]

# Icons already on the site (from Facebook), photographed earlier: one photo each is added.
# "first": the archive photo becomes the main picture (the Facebook one shows the icon only
# in a flower wreath or from afar).
ADD_PHOTOS = [
    dict(to='p1163', photo=S + '_006 Sfanta Fecioara Indurerata/icoana_02_canon-0003-2.jpg'),  # Aug 2019
    dict(to='p832', photo=S + '_005 Intampinarea Domnului/icoana_09_telefon-0001-2.jpg'),  # Aug 2019
    dict(to='p1123', photo='unsorted/20201014_131810.jpg', crop=[0.0, 0.0, 1.0, 0.9], first=True),  # Oct 2020
    dict(to='p1199', photo='unsorted/20201014_131816.jpg', crop=[0.02, 0.06, 0.96, 0.94], first=True),  # Oct 2020
    dict(to='p1091', photo='unsorted/IMG-20200521-WA0002.jpg', crop=[0.03, 0.09, 0.93, 0.91], first=True),  # May 2020
]

# Her icons in a church (2020): shown in the "for churches" section of the home page.
CHURCH_PHOTOS = [
    dict(name='biserica-1.jpg', photo=S + '_000 Biserica/Biserica large 2.jpg'),
    dict(name='biserica-2.jpg', photo=S + '_000 Biserica/Iisus.jpg'),
]

if __name__ == '__main__':
    out = {'works': WORKS, 'add_photos': ADD_PHOTOS, 'church_photos': CHURCH_PHOTOS}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'works.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(len(WORKS), 'works,', len(ADD_PHOTOS), 'added photos,', len(CHURCH_PHOTOS), 'church photos ->', path)
