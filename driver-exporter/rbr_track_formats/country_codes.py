from dataclasses import dataclass
from typing import List


@dataclass
class CountryCode:
    country: str
    alpha_2_code: str
    alpha_3_code: str
    numeric: int


country_codes: List[CountryCode] = [
    CountryCode("Afghanistan", "AF", "AFG", 4),
    CountryCode("Albania", "AL", "ALB", 8),
    CountryCode("Algeria", "DZ", "DZA", 12),
    CountryCode("American Samoa", "AS", "ASM", 16),
    CountryCode("Andorra", "AD", "AND", 20),
    CountryCode("Angola", "AO", "AGO", 24),
    CountryCode("Anguilla", "AI", "AIA", 660),
    CountryCode("Antarctica", "AQ", "ATA", 10),
    CountryCode("Antigua and Barbuda", "AG", "ATG", 28),
    CountryCode("Argentina ", "AR", "ARG", 32),
    CountryCode("Armenia", "AM", "ARM", 51),
    CountryCode("Aruba ", "AW", "ABW", 533),
    CountryCode("Australia ", "AU", "AUS", 36),
    CountryCode("Austria", "AT", "AUT", 40),
    CountryCode("Azerbaijan", "AZ", "AZE", 31),
    CountryCode("Bahamas (the) ", "BS", "BHS", 44),
    CountryCode("Bahrain", "BH", "BHR", 48),
    CountryCode("Bangladesh", "BD", "BGD", 50),
    CountryCode("Barbados", "BB", "BRB", 52),
    CountryCode("Belarus", "BY", "BLR", 112),
    CountryCode("Belgium", "BE", "BEL", 56),
    CountryCode("Belize", "BZ", "BLZ", 84),
    CountryCode("Benin ", "BJ", "BEN", 204),
    CountryCode("Bermuda", "BM", "BMU", 60),
    CountryCode("Bhutan", "BT", "BTN", 64),
    CountryCode("Bolivia (Plurinational State of)", "BO", "BOL", 68),
    CountryCode("Bonaire, Sint Eustatius and Saba", "BQ", "BES", 535),
    CountryCode("Bosnia and Herzegovina", "BA", "BIH", 70),
    CountryCode("Botswana", "BW", "BWA", 72),
    CountryCode("Bouvet Island ", "BV", "BVT", 74),
    CountryCode("Brazil", "BR", "BRA", 76),
    CountryCode("British Indian Ocean Territory (the)", "IO", "IOT", 86),
    CountryCode("Brunei Darussalam ", "BN", "BRN", 96),
    CountryCode("Bulgaria", "BG", "BGR", 100),
    CountryCode("Burkina Faso", "BF", "BFA", 854),
    CountryCode("Burundi", "BI", "BDI", 108),
    CountryCode("Cabo Verde", "CV", "CPV", 132),
    CountryCode("Cambodia", "KH", "KHM", 116),
    CountryCode("Cameroon", "CM", "CMR", 120),
    CountryCode("Canada", "CA", "CAN", 124),
    CountryCode("Cayman Islands (the)", "KY", "CYM", 136),
    CountryCode("Central African Republic (the)", "CF", "CAF", 140),
    CountryCode("Chad", "TD", "TCD", 148),
    CountryCode("Chile ", "CL", "CHL", 152),
    CountryCode("China ", "CN", "CHN", 156),
    CountryCode("Christmas Island", "CX", "CXR", 162),
    CountryCode("Cocos (Keeling) Islands (the) ", "CC", "CCK", 166),
    CountryCode("Colombia", "CO", "COL", 170),
    CountryCode("Comoros (the) ", "KM", "COM", 174),
    CountryCode("Congo (the Democratic Republic of the)", "CD", "COD", 180),
    CountryCode("Congo (the)", "CG", "COG", 178),
    CountryCode("Cook Islands (the)", "CK", "COK", 184),
    CountryCode("Costa Rica", "CR", "CRI", 188),
    CountryCode("Croatia", "HR", "HRV", 191),
    CountryCode("Cuba", "CU", "CUB", 192),
    CountryCode("Curaçao", "CW", "CUW", 531),
    CountryCode("Cyprus", "CY", "CYP", 196),
    CountryCode("Czechia", "CZ", "CZE", 203),
    CountryCode("Côte d'Ivoire ", "CI", "CIV", 384),
    CountryCode("Denmark", "DK", "DNK", 208),
    CountryCode("Djibouti", "DJ", "DJI", 262),
    CountryCode("Dominica", "DM", "DMA", 212),
    CountryCode("Dominican Republic (the)", "DO", "DOM", 214),
    CountryCode("Ecuador", "EC", "ECU", 218),
    CountryCode("Egypt ", "EG", "EGY", 818),
    CountryCode("El Salvador", "SV", "SLV", 222),
    CountryCode("Equatorial Guinea ", "GQ", "GNQ", 226),
    CountryCode("Eritrea", "ER", "ERI", 232),
    CountryCode("Estonia", "EE", "EST", 233),
    CountryCode("Eswatini", "SZ", "SWZ", 748),
    CountryCode("Ethiopia", "ET", "ETH", 231),
    CountryCode("Falkland Islands (the) [Malvinas] ", "FK", "FLK", 238),
    CountryCode("Faroe Islands (the)", "FO", "FRO", 234),
    CountryCode("Fiji", "FJ", "FJI", 242),
    CountryCode("Finland", "FI", "FIN", 246),
    CountryCode("France", "FR", "FRA", 250),
    CountryCode("French Guiana ", "GF", "GUF", 254),
    CountryCode("French Polynesia", "PF", "PYF", 258),
    CountryCode("French Southern Territories (the) ", "TF", "ATF", 260),
    CountryCode("Gabon ", "GA", "GAB", 266),
    CountryCode("Gambia (the)", "GM", "GMB", 270),
    CountryCode("Georgia", "GE", "GEO", 268),
    CountryCode("Germany", "DE", "DEU", 276),
    CountryCode("Ghana ", "GH", "GHA", 288),
    CountryCode("Gibraltar ", "GI", "GIB", 292),
    CountryCode("Greece", "GR", "GRC", 300),
    CountryCode("Greenland ", "GL", "GRL", 304),
    CountryCode("Grenada", "GD", "GRD", 308),
    CountryCode("Guadeloupe", "GP", "GLP", 312),
    CountryCode("Guam", "GU", "GUM", 316),
    CountryCode("Guatemala ", "GT", "GTM", 320),
    CountryCode("Guernsey", "GG", "GGY", 831),
    CountryCode("Guinea", "GN", "GIN", 324),
    CountryCode("Guinea-Bissau ", "GW", "GNB", 624),
    CountryCode("Guyana", "GY", "GUY", 328),
    CountryCode("Haiti ", "HT", "HTI", 332),
    CountryCode("Heard Island and McDonald Islands ", "HM", "HMD", 334),
    CountryCode("Holy See (the)", "VA", "VAT", 336),
    CountryCode("Honduras", "HN", "HND", 340),
    CountryCode("Hong Kong ", "HK", "HKG", 344),
    CountryCode("Hungary", "HU", "HUN", 348),
    CountryCode("Iceland", "IS", "ISL", 352),
    CountryCode("India ", "IN", "IND", 356),
    CountryCode("Indonesia ", "ID", "IDN", 360),
    CountryCode("Iran (Islamic Republic of)", "IR", "IRN", 364),
    CountryCode("Iraq", "IQ", "IRQ", 368),
    CountryCode("Ireland", "IE", "IRL", 372),
    CountryCode("Isle of Man", "IM", "IMN", 833),
    CountryCode("Israel", "IL", "ISR", 376),
    CountryCode("Italy ", "IT", "ITA", 380),
    CountryCode("Jamaica", "JM", "JAM", 388),
    CountryCode("Japan ", "JP", "JPN", 392),
    CountryCode("Jersey", "JE", "JEY", 832),
    CountryCode("Jordan", "JO", "JOR", 400),
    CountryCode("Kazakhstan", "KZ", "KAZ", 398),
    CountryCode("Kenya ", "KE", "KEN", 404),
    CountryCode("Kiribati", "KI", "KIR", 296),
    CountryCode("Korea (the Democratic People's Republic of)", "KP", "PRK", 408),
    CountryCode("Korea (the Republic of)", "KR", "KOR", 410),
    CountryCode("Kuwait", "KW", "KWT", 414),
    CountryCode("Kyrgyzstan", "KG", "KGZ", 417),
    CountryCode("Lao People's Democratic Republic (the)", "LA", "LAO", 418),
    CountryCode("Latvia", "LV", "LVA", 428),
    CountryCode("Lebanon", "LB", "LBN", 422),
    CountryCode("Lesotho", "LS", "LSO", 426),
    CountryCode("Liberia", "LR", "LBR", 430),
    CountryCode("Libya ", "LY", "LBY", 434),
    CountryCode("Liechtenstein ", "LI", "LIE", 438),
    CountryCode("Lithuania ", "LT", "LTU", 440),
    CountryCode("Luxembourg", "LU", "LUX", 442),
    CountryCode("Macao ", "MO", "MAC", 446),
    CountryCode("Madagascar", "MG", "MDG", 450),
    CountryCode("Malawi", "MW", "MWI", 454),
    CountryCode("Malaysia", "MY", "MYS", 458),
    CountryCode("Maldives", "MV", "MDV", 462),
    CountryCode("Mali", "ML", "MLI", 466),
    CountryCode("Malta ", "MT", "MLT", 470),
    CountryCode("Marshall Islands (the)", "MH", "MHL", 584),
    CountryCode("Martinique", "MQ", "MTQ", 474),
    CountryCode("Mauritania", "MR", "MRT", 478),
    CountryCode("Mauritius ", "MU", "MUS", 480),
    CountryCode("Mayotte", "YT", "MYT", 175),
    CountryCode("Mexico", "MX", "MEX", 484),
    CountryCode("Micronesia (Federated States of)", "FM", "FSM", 583),
    CountryCode("Moldova (the Republic of) ", "MD", "MDA", 498),
    CountryCode("Monaco", "MC", "MCO", 492),
    CountryCode("Mongolia", "MN", "MNG", 496),
    CountryCode("Montenegro", "ME", "MNE", 499),
    CountryCode("Montserrat", "MS", "MSR", 500),
    CountryCode("Morocco", "MA", "MAR", 504),
    CountryCode("Mozambique", "MZ", "MOZ", 508),
    CountryCode("Myanmar", "MM", "MMR", 104),
    CountryCode("Namibia", "NA", "NAM", 516),
    CountryCode("Nauru ", "NR", "NRU", 520),
    CountryCode("Nepal ", "NP", "NPL", 524),
    CountryCode("Netherlands (the) ", "NL", "NLD", 528),
    CountryCode("New Caledonia ", "NC", "NCL", 540),
    CountryCode("New Zealand", "NZ", "NZL", 554),
    CountryCode("Nicaragua ", "NI", "NIC", 558),
    CountryCode("Niger (the)", "NE", "NER", 562),
    CountryCode("Nigeria", "NG", "NGA", 566),
    CountryCode("Niue", "NU", "NIU", 570),
    CountryCode("Norfolk Island", "NF", "NFK", 574),
    CountryCode("Northern Mariana Islands (the)", "MP", "MNP", 580),
    CountryCode("Norway", "NO", "NOR", 578),
    CountryCode("Oman", "OM", "OMN", 512),
    CountryCode("Pakistan", "PK", "PAK", 586),
    CountryCode("Palau ", "PW", "PLW", 585),
    CountryCode("Palestine, State of", "PS", "PSE", 275),
    CountryCode("Panama", "PA", "PAN", 591),
    CountryCode("Papua New Guinea", "PG", "PNG", 598),
    CountryCode("Paraguay", "PY", "PRY", 600),
    CountryCode("Peru", "PE", "PER", 604),
    CountryCode("Philippines (the) ", "PH", "PHL", 608),
    CountryCode("Pitcairn", "PN", "PCN", 612),
    CountryCode("Poland", "PL", "POL", 616),
    CountryCode("Portugal", "PT", "PRT", 620),
    CountryCode("Puerto Rico", "PR", "PRI", 630),
    CountryCode("Qatar ", "QA", "QAT", 634),
    CountryCode("Republic of North Macedonia", "MK", "MKD", 807),
    CountryCode("Romania", "RO", "ROU", 642),
    CountryCode("Russian Federation (the)", "RU", "RUS", 643),
    CountryCode("Rwanda", "RW", "RWA", 646),
    CountryCode("Réunion", "RE", "REU", 638),
    CountryCode("Saint Barthélemy", "BL", "BLM", 652),
    CountryCode("Saint Helena, Ascension and Tristan da Cunha", "SH", "SHN", 654),
    CountryCode("Saint Kitts and Nevis ", "KN", "KNA", 659),
    CountryCode("Saint Lucia", "LC", "LCA", 662),
    CountryCode("Saint Martin (French part)", "MF", "MAF", 663),
    CountryCode("Saint Pierre and Miquelon ", "PM", "SPM", 666),
    CountryCode("Saint Vincent and the Grenadines", "VC", "VCT", 670),
    CountryCode("Samoa ", "WS", "WSM", 882),
    CountryCode("San Marino", "SM", "SMR", 674),
    CountryCode("Sao Tome and Principe ", "ST", "STP", 678),
    CountryCode("Saudi Arabia", "SA", "SAU", 682),
    CountryCode("Senegal", "SN", "SEN", 686),
    CountryCode("Serbia", "RS", "SRB", 688),
    CountryCode("Seychelles", "SC", "SYC", 690),
    CountryCode("Sierra Leone", "SL", "SLE", 694),
    CountryCode("Singapore ", "SG", "SGP", 702),
    CountryCode("Sint Maarten (Dutch part) ", "SX", "SXM", 534),
    CountryCode("Slovakia", "SK", "SVK", 703),
    CountryCode("Slovenia", "SI", "SVN", 705),
    CountryCode("Solomon Islands", "SB", "SLB", 90),
    CountryCode("Somalia", "SO", "SOM", 706),
    CountryCode("South Africa", "ZA", "ZAF", 710),
    CountryCode("South Georgia and the South Sandwich Islands", "GS", "SGS", 239),
    CountryCode("South Sudan", "SS", "SSD", 728),
    CountryCode("Spain ", "ES", "ESP", 724),
    CountryCode("Sri Lanka ", "LK", "LKA", 144),
    CountryCode("Sudan (the)", "SD", "SDN", 729),
    CountryCode("Suriname", "SR", "SUR", 740),
    CountryCode("Svalbard and Jan Mayen", "SJ", "SJM", 744),
    CountryCode("Sweden", "SE", "SWE", 752),
    CountryCode("Switzerland", "CH", "CHE", 756),
    CountryCode("Syrian Arab Republic", "SY", "SYR", 760),
    CountryCode("Taiwan (Province of China)", "TW", "TWN", 158),
    CountryCode("Tajikistan", "TJ", "TJK", 762),
    CountryCode("Tanzania, United Republic of", "TZ", "TZA", 834),
    CountryCode("Thailand", "TH", "THA", 764),
    CountryCode("Timor-Leste", "TL", "TLS", 626),
    CountryCode("Togo", "TG", "TGO", 768),
    CountryCode("Tokelau", "TK", "TKL", 772),
    CountryCode("Tonga ", "TO", "TON", 776),
    CountryCode("Trinidad and Tobago", "TT", "TTO", 780),
    CountryCode("Tunisia", "TN", "TUN", 788),
    CountryCode("Turkey", "TR", "TUR", 792),
    CountryCode("Turkmenistan", "TM", "TKM", 795),
    CountryCode("Turks and Caicos Islands (the)", "TC", "TCA", 796),
    CountryCode("Tuvalu", "TV", "TUV", 798),
    CountryCode("Uganda", "UG", "UGA", 800),
    CountryCode("Ukraine", "UA", "UKR", 804),
    CountryCode("United Arab Emirates (the)", "AE", "ARE", 784),
    CountryCode(
        "United Kingdom of Great Britain and Northern Ireland (the)", "GB", "GBR", 826
    ),
    CountryCode("United States Minor Outlying Islands (the)", "UM", "UMI", 581),
    CountryCode("United States of America (the)", "US", "USA", 840),
    CountryCode("Uruguay", "UY", "URY", 858),
    CountryCode("Uzbekistan", "UZ", "UZB", 860),
    CountryCode("Vanuatu", "VU", "VUT", 548),
    CountryCode("Venezuela (Bolivarian Republic of)", "VE", "VEN", 862),
    CountryCode("Viet Nam", "VN", "VNM", 704),
    CountryCode("Virgin Islands (British)", "VG", "VGB", 92),
    CountryCode("Virgin Islands (U.S.) ", "VI", "VIR", 850),
    CountryCode("Wallis and Futuna ", "WF", "WLF", 876),
    CountryCode("Western Sahara", "EH", "ESH", 732),
    CountryCode("Yemen ", "YE", "YEM", 887),
    CountryCode("Zambia", "ZM", "ZMB", 894),
    CountryCode("Zimbabwe", "ZW", "ZWE", 716),
    CountryCode("Åland Islands ", "AX", "ALA", 248),
]
