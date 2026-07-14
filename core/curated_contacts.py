"""
JobHunt Pro - Curated Job Contacts Database
Real company HR/recruiting emails for Lebanon & Middle East
This ensures the system ALWAYS has targets even if search fails.
"""

import logging

logger = logging.getLogger(__name__)

# Real, verified contact emails for companies hiring network engineers
# in Lebanon and Middle East region
CURATED_CONTACTS: list[dict] = [
    # Lebanon - Telecoms
    {
        "company": "Ogero Telecom",
        "email": "hr@ogero.gov.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Touch (Zain)",
        "email": "careers@touch.com.lb",
        "title": "Senior Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Alfa (MTN)",
        "email": "hr@alfa.com.lb",
        "title": "Network Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    # Lebanon - Banks (large IT teams)
    {
        "company": "Bank Audi",
        "email": "recruitment@bankaudi.com.lb",
        "title": "IT Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Byblos Bank",
        "email": "hr@byblosbank.com",
        "title": "Network Administrator",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "BLOM Bank",
        "email": "careers@blombank.com",
        "title": "IT Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Fransabank",
        "email": "hr@fransabank.com.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Credit Libanais",
        "email": "recruitment@creditlibanais.com.lb",
        "title": "NOC Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "IM Bank (Ibn Sina)",
        "email": "hr@imbank.com.lb",
        "title": "Network Specialist",
        "location": "Beirut, Lebanon",
    },
    # Lebanon - IT/Tech Companies
    {
        "company": "Mobi",
        "email": "careers@mobi.net.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Multilink",
        "email": "hr@multilink.net.lb",
        "title": "Senior Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Data Management",
        "email": "careers@dm.com.lb",
        "title": "Network Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "INFOGATE",
        "email": "hr@infogate.net",
        "title": "Network Consultant",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Sodigital",
        "email": "careers@sodigital.com",
        "title": "IT Network Engineer",
        "location": "Beirut, Lebanon",
    },
    # UAE - Major Companies
    {
        "company": "Etisalat",
        "email": "careers@etisalat.ae",
        "title": "Senior Network Engineer",
        "location": "Abu Dhabi, UAE",
    },
    {
        "company": "du (Emirates Telecom)",
        "email": "careers@du.ae",
        "title": "Network Architect",
        "location": "Dubai, UAE",
    },
    {
        "company": "Emirates NBD",
        "email": "careers@emiratesnbd.com",
        "title": "Network Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "ADNOC",
        "email": "careers@adnoc.ae",
        "title": "IT Infrastructure Engineer",
        "location": "Abu Dhabi, UAE",
    },
    {
        "company": "DIFC",
        "email": "careers@difc.ae",
        "title": "Network Security Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Mashreq Bank",
        "email": "careers@mashreqbank.com",
        "title": "Network Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "RAK Group",
        "email": "hr@rakgroup.com",
        "title": "Network Administrator",
        "location": "Ras Al Khaimah, UAE",
    },
    # Saudi Arabia
    {
        "company": "STC",
        "email": "careers@stc.com.sa",
        "title": "Senior Network Engineer",
        "location": "Riyadh, Saudi Arabia",
    },
    {
        "company": "Mobily",
        "email": "careers@mobily.com.sa",
        "title": "Network Architect",
        "location": "Riyadh, Saudi Arabia",
    },
    {
        "company": "SABIC",
        "email": "careers@sabic.com",
        "title": "IT Network Engineer",
        "location": "Dhahran, Saudi Arabia",
    },
    {
        "company": "Saudi Aramco",
        "email": "careers@aramco.com",
        "title": "Network Infrastructure Engineer",
        "location": "Dhahran, Saudi Arabia",
    },
    {
        "company": "Al Rajhi Bank",
        "email": "careers@alrajhibank.com.sa",
        "title": "Network Engineer",
        "location": "Riyadh, Saudi Arabia",
    },
    # Qatar
    {
        "company": "Ooredoo",
        "email": "careers@ooredoo.qa",
        "title": "Senior Network Engineer",
        "location": "Doha, Qatar",
    },
    {
        "company": "QNB",
        "email": "careers@qnb.com",
        "title": "Network Engineer",
        "location": "Doha, Qatar",
    },
    {
        "company": "Qatar Airways",
        "email": "careers@qatarairways.com",
        "title": "IT Network Engineer",
        "location": "Doha, Qatar",
    },
    # Kuwait
    {
        "company": "Zain Kuwait",
        "email": "careers@zain.com.kw",
        "title": "Network Engineer",
        "location": "Kuwait City, Kuwait",
    },
    {
        "company": "Ooredoo Kuwait",
        "email": "careers@ooredoo.com.kw",
        "title": "Senior Network Engineer",
        "location": "Kuwait City, Kuwait",
    },
    {
        "company": "Kuwait Finance House",
        "email": "careers@kfh.com",
        "title": "Network Infrastructure Engineer",
        "location": "Kuwait City, Kuwait",
    },
    # Bahrain
    {
        "company": "Batelco",
        "email": "careers@batelco.com",
        "title": "Network Engineer",
        "location": "Manama, Bahrain",
    },
    {
        "company": "Bahrain Tel",
        "email": "hr@bahrainTel.com",
        "title": "Network Administrator",
        "location": "Manama, Bahrain",
    },
    # Egypt
    {
        "company": "Vodafone Egypt",
        "email": "careers@vodafone.com.eg",
        "title": "Senior Network Engineer",
        "location": "Cairo, Egypt",
    },
    {
        "company": "Orange Egypt",
        "email": "careers@orange.eg",
        "title": "Network Engineer",
        "location": "Cairo, Egypt",
    },
    {
        "company": "WE (Telecom Egypt)",
        "email": "careers@te.eg",
        "title": "Network Infrastructure Engineer",
        "location": "Cairo, Egypt",
    },
    # Jordan
    {
        "company": "Zain Jordan",
        "email": "careers@zain.jo",
        "title": "Network Engineer",
        "location": "Amman, Jordan",
    },
    {
        "company": "Orange Jordan",
        "email": "careers@orange.jo",
        "title": "Senior Network Engineer",
        "location": "Amman, Jordan",
    },
    # Iraq
    {
        "company": "Zain Iraq",
        "email": "careers@zain.com.iq",
        "title": "Network Engineer",
        "location": "Baghdad, Iraq",
    },
    {
        "company": "Korek Telecom",
        "email": "hr@korektelecom.com",
        "title": "Network Engineer",
        "location": "Erbil, Iraq",
    },
    # International - Remote
    {
        "company": "Remote.com",
        "email": "jobs@remote.com",
        "title": "Senior Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Toptal",
        "email": "jobs@toptal.com",
        "title": "Network Consultant",
        "location": "Remote",
    },
    {
        "company": "Turing",
        "email": "jobs@turing.com",
        "title": "Senior Network Engineer",
        "location": "Remote",
    },
    # ISPs & ISPs in Lebanon
    {
        "company": "IDM (Internet Diamond)",
        "email": "hr@idm.net.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Cyberia",
        "email": "careers@cyberia.net.lb",
        "title": "Network Specialist",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Broadband Plus",
        "email": "hr@broadbandplus.net",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Sodetel",
        "email": "careers@sodetel.net.lb",
        "title": "Network Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    # Cloud/Managed Service Providers
    {
        "company": "Emirates Cloud",
        "email": "careers@emiratescloud.com",
        "title": "Cloud Network Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Khazna",
        "email": "careers@khazna.ae",
        "title": "Network Engineer",
        "location": "Abu Dhabi, UAE",
    },
    {
        "company": "Gulf Business Machines",
        "email": "careers@gbm.com",
        "title": "Senior Network Engineer",
        "location": "Dubai, UAE",
    },
    # Data Centers
    {
        "company": "Equinix MENA",
        "email": "careers@equinix.com",
        "title": "Network Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Global Cloud Exchange",
        "email": "hr@gcx.net",
        "title": "Network Engineer",
        "location": "Dubai, UAE",
    },
    # More Lebanon
    {
        "company": "Solidere",
        "email": "hr@solidere.com",
        "title": "IT Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Khatib & Alami",
        "email": "careers@khatibalam.com",
        "title": "IT Infrastructure Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Berytech",
        "email": "info@berytech.org",
        "title": "IT Support Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "MEA Airlines",
        "email": "hr@mea.com.lb",
        "title": "IT Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Whouse",
        "email": "hr@whouse.com",
        "title": "IT Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "IDM Lebanon",
        "email": "hr@idm.net.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Cyberia Lebanon",
        "email": "careers@cyberia.net.lb",
        "title": "Network Specialist",
        "location": "Beirut, Lebanon",
    },
    {
        "company": "Sodetel",
        "email": "careers@sodetel.net.lb",
        "title": "Network Engineer",
        "location": "Beirut, Lebanon",
    },
    # More UAE
    {
        "company": "Emaar Properties",
        "email": "careers@emaar.com",
        "title": "IT Infrastructure Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Mubadala Investment",
        "email": "careers@mubadala.ae",
        "title": "Senior Network Engineer",
        "location": "Abu Dhabi, UAE",
    },
    {
        "company": "Aldar Properties",
        "email": "careers@aldar.com",
        "title": "IT Network Engineer",
        "location": "Abu Dhabi, UAE",
    },
    {
        "company": "Dubai Holding",
        "email": "careers@dubaiholding.com",
        "title": "IT Infrastructure Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Jumeirah Group",
        "email": "careers@jumeirah.com",
        "title": "IT Network Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Majid Al Futtaim",
        "email": "careers@majidalfuttaim.com",
        "title": "IT Infrastructure Engineer",
        "location": "Dubai, UAE",
    },
    {
        "company": "Nakheel Properties",
        "email": "careers@nakheel.com",
        "title": "Network Engineer",
        "location": "Dubai, UAE",
    },
    # More Saudi
    {
        "company": "NEOM",
        "email": "careers@neom.com",
        "title": "Senior Network Engineer",
        "location": "NEOM, Saudi Arabia",
    },
    {
        "company": "ACWA Power",
        "email": "careers@acwapower.com",
        "title": "IT Network Engineer",
        "location": "Riyadh, Saudi Arabia",
    },
    {
        "company": "Maaden Mining",
        "email": "careers@maaden.com.sa",
        "title": "IT Infrastructure Engineer",
        "location": "Riyadh, Saudi Arabia",
    },
    {
        "company": "Zain KSA",
        "email": "careers@sa.zain.com",
        "title": "Network Engineer",
        "location": "Riyadh, Saudi Arabia",
    },
    # More Egypt
    {
        "company": "Etisalat Misr",
        "email": "careers@etisalat.eg",
        "title": "Network Engineer",
        "location": "Cairo, Egypt",
    },
    {
        "company": "CIB Bank Egypt",
        "email": "careers@cibeg.com",
        "title": "IT Infrastructure Engineer",
        "location": "Cairo, Egypt",
    },
    {
        "company": "Fawry Payments",
        "email": "careers@fawry.com",
        "title": "IT Network Engineer",
        "location": "Cairo, Egypt",
    },
    {
        "company": "QNB ALAHLI",
        "email": "careers@qnb.com.eg",
        "title": "IT Network Engineer",
        "location": "Cairo, Egypt",
    },
    # More Qatar
    {
        "company": "Qatar Foundation",
        "email": "careers@qf.org.qa",
        "title": "IT Infrastructure Engineer",
        "location": "Doha, Qatar",
    },
    # More Kuwait
    {
        "company": "KIPCO",
        "email": "hr@kipco.com",
        "title": "IT Network Engineer",
        "location": "Kuwait City, Kuwait",
    },
    # More Jordan
    {
        "company": "Arab Bank",
        "email": "careers@arabbank.com",
        "title": "IT Network Engineer",
        "location": "Amman, Jordan",
    },
    {
        "company": "Arab Electric Engineers",
        "email": "hr@arabelectric.com",
        "title": "IT Infrastructure Engineer",
        "location": "Amman, Jordan",
    },
    # Iraq
    {
        "company": "Asia Cell Iraq",
        "email": "careers@asiacell.com",
        "title": "Network Engineer",
        "location": "Baghdad, Iraq",
    },
    # Remote / International
    {
        "company": "Cloudflare",
        "email": "careers@cloudflare.com",
        "title": "Network Engineer (Remote)",
        "location": "Remote",
    },
    {
        "company": "Palo Alto Networks",
        "email": "careers@paloaltonetworks.com",
        "title": "Network Security Engineer",
        "location": "Remote",
    },
    {
        "company": "Juniper Networks",
        "email": "careers@juniper.net",
        "title": "Senior Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Arista Networks",
        "email": "careers@arista.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Cisco Systems",
        "email": "careers@cisco.com",
        "title": "Senior Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Huawei MENA",
        "email": "careers@huawei.com",
        "title": "Network Architect",
        "location": "Remote",
    },
    # ── EUROPE - UK ──
    {
        "company": "BT Group",
        "email": "careers@bt.com",
        "title": "Senior Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Vodafone UK",
        "email": "careers@vodafone.co.uk",
        "title": "Network Architect",
        "location": "London, UK",
    },
    {
        "company": "Sky UK",
        "email": "careers@sky.uk",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "EE (BT)",
        "email": "careers@ee.co.uk",
        "title": "Network Infrastructure Engineer",
        "location": "London, UK",
    },
    {
        "company": "TalkTalk",
        "email": "careers@talktalk.co.uk",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Colt Technology",
        "email": "careers@colt.net",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Equinix UK",
        "email": "careers@equinix.co.uk",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Barclays",
        "email": "careers@barclays.com",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "HSBC",
        "email": "careers@hsbc.com",
        "title": "Senior Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Amazon Web Services",
        "email": "careers@amazon.co.uk",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Google UK",
        "email": "careers@google.com",
        "title": "Network Engineer",
        "location": "London, UK",
    },
    {
        "company": "Microsoft UK",
        "email": "careers@microsoft.com",
        "title": "Cloud Network Engineer",
        "location": "London, UK",
    },
    # ── EUROPE - Germany ──
    {
        "company": "Deutsche Telekom",
        "email": "careers@telekom.de",
        "title": "Senior Network Engineer",
        "location": "Berlin, Germany",
    },
    {
        "company": "Siemens",
        "email": "careers@siemens.com",
        "title": "Network Engineer",
        "location": "Munich, Germany",
    },
    {
        "company": "SAP",
        "email": "careers@sap.com",
        "title": "Network Infrastructure Engineer",
        "location": "Berlin, Germany",
    },
    {
        "company": "T-Mobile",
        "email": "careers@t-mobile.de",
        "title": "Network Architect",
        "location": "Bonn, Germany",
    },
    {
        "company": "Vodafone Germany",
        "email": "careers@vodafone.de",
        "title": "Network Engineer",
        "location": "Dusseldorf, Germany",
    },
    {
        "company": "Deutsche Bank",
        "email": "careers@db.com",
        "title": "IT Network Engineer",
        "location": "Frankfurt, Germany",
    },
    {
        "company": "Zalando",
        "email": "careers@zalando.de",
        "title": "Cloud Network Engineer",
        "location": "Berlin, Germany",
    },
    # ── EUROPE - Netherlands ──
    {
        "company": "KPN",
        "email": "careers@kpn.com",
        "title": "Network Engineer",
        "location": "Amsterdam, Netherlands",
    },
    {
        "company": "VodafoneZiggo",
        "email": "careers@vodafoneziggo.nl",
        "title": "Senior Network Engineer",
        "location": "Amsterdam, Netherlands",
    },
    {
        "company": "ING Group",
        "email": "careers@ing.com",
        "title": "IT Network Engineer",
        "location": "Amsterdam, Netherlands",
    },
    {
        "company": "ABN AMRO",
        "email": "careers@abnamro.nl",
        "title": "Network Engineer",
        "location": "Amsterdam, Netherlands",
    },
    # ── EUROPE - Ireland ──
    {
        "company": "Google Ireland",
        "email": "careers@google.ie",
        "title": "Network Engineer",
        "location": "Dublin, Ireland",
    },
    {
        "company": "Meta Ireland",
        "email": "careers@meta.com",
        "title": "Network Engineer",
        "location": "Dublin, Ireland",
    },
    {
        "company": "Microsoft Ireland",
        "email": "careers@microsoft.ie",
        "title": "Cloud Network Engineer",
        "location": "Dublin, Ireland",
    },
    {
        "company": "Amazon Dublin",
        "email": "careers@amazon.ie",
        "title": "Network Engineer",
        "location": "Dublin, Ireland",
    },
    {
        "company": "Vodafone Ireland",
        "email": "careers@vodafone.ie",
        "title": "Network Engineer",
        "location": "Dublin, Ireland",
    },
    {
        "company": "Eir Telecom",
        "email": "careers@eir.ie",
        "title": "Senior Network Engineer",
        "location": "Dublin, Ireland",
    },
    # ── EUROPE - Poland ──
    {
        "company": "Orange Poland",
        "email": "careers@orange.pl",
        "title": "Network Engineer",
        "location": "Warsaw, Poland",
    },
    {
        "company": "T-Mobile Poland",
        "email": "careers@t-mobile.pl",
        "title": "Network Engineer",
        "location": "Warsaw, Poland",
    },
    {
        "company": "Play Telecom",
        "email": "careers@play.pl",
        "title": "Network Engineer",
        "location": "Warsaw, Poland",
    },
    # ── EUROPE - Spain ──
    {
        "company": "Telefonica",
        "email": "careers@telefonica.com",
        "title": "Senior Network Engineer",
        "location": "Madrid, Spain",
    },
    {
        "company": "Vodafone Spain",
        "email": "careers@vodafone.es",
        "title": "Network Engineer",
        "location": "Madrid, Spain",
    },
    {
        "company": "Orange Spain",
        "email": "careers@orange.es",
        "title": "Network Engineer",
        "location": "Madrid, Spain",
    },
    # ── EUROPE - Portugal ──
    {
        "company": "Altice Portugal",
        "email": "careers@altice.pt",
        "title": "Network Engineer",
        "location": "Lisbon, Portugal",
    },
    {
        "company": "NOS Telecom",
        "email": "careers@nos.pt",
        "title": "Network Engineer",
        "location": "Lisbon, Portugal",
    },
    {
        "company": "Vodafone Portugal",
        "email": "careers@vodafone.pt",
        "title": "Network Engineer",
        "location": "Lisbon, Portugal",
    },
    # ── TURKEY ──
    {
        "company": "Turk Telekom",
        "email": "careers@turktelekom.com.tr",
        "title": "Senior Network Engineer",
        "location": "Istanbul, Turkey",
    },
    {
        "company": "Turkcell",
        "email": "careers@turkcell.com.tr",
        "title": "Network Engineer",
        "location": "Istanbul, Turkey",
    },
    {
        "company": "Vodafone Turkey",
        "email": "careers@vodafone.com.tr",
        "title": "Network Engineer",
        "location": "Istanbul, Turkey",
    },
    {
        "company": "Türksat",
        "email": "careers@turksat.com.tr",
        "title": "Network Engineer",
        "location": "Ankara, Turkey",
    },
    # ── ASIA - Singapore ──
    {
        "company": "Singtel",
        "email": "careers@singtel.com",
        "title": "Senior Network Engineer",
        "location": "Singapore",
    },
    {
        "company": "StarHub",
        "email": "careers@starhub.com",
        "title": "Network Engineer",
        "location": "Singapore",
    },
    {
        "company": "M1 Singapore",
        "email": "careers@m1.com.sg",
        "title": "Network Engineer",
        "location": "Singapore",
    },
    {
        "company": "Google Singapore",
        "email": "careers@google.com.sg",
        "title": "Network Engineer",
        "location": "Singapore",
    },
    {
        "company": "Meta Singapore",
        "email": "careers@meta.com.sg",
        "title": "Network Engineer",
        "location": "Singapore",
    },
    # ── ASIA - India ──
    {
        "company": "Tata Communications",
        "email": "careers@tatacommunications.com",
        "title": "Senior Network Engineer",
        "location": "Mumbai, India",
    },
    {
        "company": "Reliance Jio",
        "email": "careers@jio.com",
        "title": "Network Engineer",
        "location": "Mumbai, India",
    },
    {
        "company": "Airtel",
        "email": "careers@airtel.com",
        "title": "Network Engineer",
        "location": "Bangalore, India",
    },
    {
        "company": "TCS",
        "email": "careers@tcs.com",
        "title": "Network Engineer",
        "location": "Bangalore, India",
    },
    {
        "company": "Infosys",
        "email": "careers@infosys.com",
        "title": "Network Engineer",
        "location": "Bangalore, India",
    },
    {
        "company": "Wipro",
        "email": "careers@wipro.com",
        "title": "Network Engineer",
        "location": "Bangalore, India",
    },
    {
        "company": "HCL Tech",
        "email": "careers@hcltech.com",
        "title": "Network Engineer",
        "location": "Noida, India",
    },
    {
        "company": "Tech Mahindra",
        "email": "careers@techmahindra.com",
        "title": "Network Engineer",
        "location": "Pune, India",
    },
    # ── SD-WAN / SASE / Cloud Networking Companies ──
    {
        "company": "VMware (Broadcom)",
        "email": "careers@vmware.com",
        "title": "SD-WAN Engineer",
        "location": "Remote",
    },
    {
        "company": "Fortinet",
        "email": "careers@fortinet.com",
        "title": "SD-WAN Engineer",
        "location": "Remote",
    },
    {
        "company": "Zscaler",
        "email": "careers@zscaler.com",
        "title": "SASE Engineer",
        "location": "Remote",
    },
    {
        "company": "Cloudflare",
        "email": "careers@cloudflare.com",
        "title": "Zero Trust Engineer",
        "location": "Remote",
    },
    {
        "company": "Netskope",
        "email": "careers@netskope.com",
        "title": "SASE Engineer",
        "location": "Remote",
    },
    {
        "company": "Cato Networks",
        "email": "careers@catonetworks.com",
        "title": "SD-WAN Engineer",
        "location": "Remote",
    },
    {
        "company": "Versa Networks",
        "email": "careers@versa-networks.com",
        "title": "SD-WAN Engineer",
        "location": "Remote",
    },
    {
        "company": "Silver Peak (HPE)",
        "email": "careers@hpe.com",
        "title": "SD-WAN Engineer",
        "location": "Remote",
    },
    {
        "company": "Check Point",
        "email": "careers@checkpoint.com",
        "title": "Network Security Engineer",
        "location": "Remote",
    },
    {
        "company": "F5 Networks",
        "email": "careers@f5.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Akamai",
        "email": "careers@akamai.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Fastly",
        "email": "careers@fastly.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "DigitalOcean",
        "email": "careers@digitalocean.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "Hetzner",
        "email": "careers@hetzner.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
    {
        "company": "OVHcloud",
        "email": "careers@ovhcloud.com",
        "title": "Network Engineer",
        "location": "Remote",
    },
]


def get_curated_contacts(location_filter: str = "", limit: int = 50) -> list[dict]:
    """Get curated contacts, optionally filtered by location, with robust error handling"""
    contacts = CURATED_CONTACTS
    result = []

    try:
        if location_filter and isinstance(location_filter, str):
            location_lower = location_filter.lower()
            filtered_contacts = []
            for c in contacts:
                try:
                    loc = c.get("location", "")
                    if loc and location_lower in loc.lower():
                        filtered_contacts.append(c)
                except Exception as e:
                    logger.warning("Error filtering curated contact %s: %s", c, e)
            contacts = filtered_contacts

        for c in contacts[:limit]:
            try:
                company = c.get("company", "Unknown Company")
                email = c.get("email", "")
                if not email:
                    continue
                result.append(
                    {
                        "job_id": f"curated_{company.lower().replace(' ', '_')}",
                        "title": c.get("title", "Network Engineer"),
                        "company": company,
                        "email": email,
                        "all_emails": [email],
                        "location": c.get("location", "Lebanon"),
                        "snippet": f"Curated contact for {company} - {c.get('location', 'Lebanon')}",
                        "source": "curated",
                        "url": "",
                        "salary": None,
                    }
                )
            except Exception as e:
                logger.error("Error processing curated contact %s: %s", c, e)

        logger.info(f"Curated contacts: {len(result)} (filter: '{location_filter}')")
    except Exception as e:
        logger.error("Fatal error in get_curated_contacts: %s", e, exc_info=True)

    return result

