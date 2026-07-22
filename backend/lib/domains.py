DOMAIN_ALLOWLIST = {
    "primary_source": [
        "ccel.org",                    # Christian Classics Ethereal Library — patristic/historical texts
        "biblehub.com",                # interlinear, lexicons, cross-referenced commentaries
        "blueletterbible.org",         # original language tools, Strong's, multi-commentary
        "biblegateway.com",            # multiple translations
        "earlychristianwritings.com",  # early Christian primary texts
    ],
    "academic_neutral": [
        "bibleodyssey.org",         # Society of Biblical Literature's public-facing site;
                                    # explicitly nonsectarian, not affiliated with any
                                    # religious or political body — closest thing to a
                                    # true neutral academic source in this list
        "sbl-site.org",             # Society of Biblical Literature (main site)
        "biblicalstudies.org.uk",   # Tyndale House archive; broad scholarly coverage but
                                    # evangelical-affiliated host — treat as neutral-leaning,
                                    # not neutral
    ],
    "catholic": [
        "vatican.va",             # The Holy See — official
        "usccb.org",              # United States Conference of Catholic Bishops — official
        "newadvent.org",          # Catholic Encyclopedia + Church Fathers primary texts
        "catholic.com",           # Catholic Answers — widely used apologetics/reference
        "ewtn.com",
        "papalencyclicals.net",   # archive of papal and magisterial documents
    ],
    "orthodox": [
        "oca.org",             # Orthodox Church in America — official, autocephalous
        "goarch.org",          # Greek Orthodox Archdiocese of America — official
        "antiochian.org",      # Antiochian Orthodox Christian Archdiocese — official
        "ancientfaith.com",    # major Orthodox media network, widely cited as trustworthy
        "svots.edu",           # St. Vladimir's Orthodox Theological Seminary — leading
                                # Orthodox academic institution
        "publicorthodoxy.org", # Orthodox Christian Studies Center (Fordham) — academic
        "orthodoxwiki.org",    # useful reference, but wiki-editable — lower confidence,
                                # prefer the above when they cover the same ground
    ],
    "reformed": [
        "ligonier.org",           # Ligonier Ministries (R.C. Sproul)
        "monergism.com",          # one of the largest curated Reformed text archives
        "thegospelcoalition.org", # broad Reformed/evangelical network
        "desiringgod.org",        # John Piper
        "gty.org",                # Grace to You (John MacArthur)
        "opc.org",                # Orthodox Presbyterian Church — official, confessional
        "pcaac.org",              # Presbyterian Church in America — official
        "reformedstandards.com",  # confessions/catechisms (Westminster, Three Forms of Unity) —
                                   # primary-source-adjacent, kept in this tier since the
                                   # documents themselves are Reformed-specific
    ],
    "lutheran": [
        "lcms.org",           # Lutheran Church—Missouri Synod — official, confessional/conservative
        "elca.org",           # Evangelical Lutheran Church in America — official, mainline
        "wels.net",           # Wisconsin Evangelical Lutheran Synod — official, confessional
        "bookofconcord.org",  # the Lutheran confessions — primary source
    ],
    "wesleyan_methodist": [
        "umc.org",             # United Methodist Church — official
        "globalmethodist.org", # Global Methodist Church — official (formed 2022, more
                                # conservative UMC-descendant body; include for balance)
        "wesleyan.org",        # The Wesleyan Church — official
        "nazarene.org",        # Church of the Nazarene — official
        "seedbed.com",         # Asbury-affiliated Wesleyan publisher
        "wesley.nnu.edu",      # Wesley Center Online — primary texts of John & Charles Wesley
    ],
    "baptist": [
        "sbc.net",         # Southern Baptist Convention — official
        "bfm.sbc.net",     # Baptist Faith & Message — SBC's confessional statement, primary source
        "sbts.edu",        # Southern Baptist Theological Seminary — major SBC academic institution
        "abc-usa.org",     # American Baptist Churches USA — official, more moderate/progressive
                            # counterpart to the SBC; include for denominational balance
        "founders.org",    # Reformed Baptist
    ],
    "anglican": [
        "anglicancommunion.org",  # official, worldwide Anglican Communion
        "churchofengland.org",    # Church of England — official
        "episcopalchurch.org",    # The Episcopal Church (US province) — official
        "anglicansonline.org",    # independent, long-running hub — widely read by Anglican clergy
        "projectcanterbury.org",  # primary texts of the Oxford Movement and classical Anglicanism
    ],
    "pentecostal_charismatic": [
        "ag.org",       # Assemblies of God — official, largest global Pentecostal body
        "cogic.org",    # Church of God in Christ — official, major historically Black Pentecostal body
        "foursquare.org",  # International Church of the Foursquare Gospel — official
        "iphc.org",     # International Pentecostal Holiness Church — official
    ],
    # Broadly evangelical, cross-denominational in practice but with a
    # general-Protestant lean — do not use as the sole source for
    # neutral_baseline steps.
    "general_evangelical": [
        "gotquestions.org",
        "str.org",
        "bible.org",
    ],
}