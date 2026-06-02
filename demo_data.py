"""
Sample data used when no API key is set, so the app still works.
Now shaped as 10 eras; each "imageQuery" is used to pull real photos from
Wikimedia Commons at runtime. With a real API key, the app generates this for
ANY country you type.
"""

DEMO_HISTORY = {
    "country": "Egypt (sample)",
    "eras": [
        {
            "title": "Predynastic Egypt",
            "period": "c. 6000-3100 BCE",
            "summary": "Farming communities settled along the Nile, developing pottery, trade, and early religion. Over millennia they grew into the kingdoms of Upper and Lower Egypt.",
            "imageQuery": "Predynastic Egypt pottery Naqada",
        },
        {
            "title": "Early Dynastic Period",
            "period": "c. 3100-2686 BCE",
            "summary": "King Narmer unified Upper and Lower Egypt into a single state, founding the institution of the pharaoh. Writing, art, and royal tombs at Abydos flourished.",
            "imageQuery": "Narmer Palette",
        },
        {
            "title": "Old Kingdom — Age of Pyramids",
            "period": "c. 2686-2181 BCE",
            "summary": "A powerful centralized state built the great pyramids at Giza as royal tombs. It was an era of monumental architecture and advanced engineering.",
            "imageQuery": "Great Pyramid of Giza",
        },
        {
            "title": "Middle Kingdom",
            "period": "c. 2055-1650 BCE",
            "summary": "After a period of division, Egypt was reunified and entered a golden age of literature and art, expanding trade and influence into Nubia.",
            "imageQuery": "Middle Kingdom Egypt statue",
        },
        {
            "title": "New Kingdom — Imperial Egypt",
            "period": "c. 1550-1077 BCE",
            "summary": "Egypt became a dominant empire under pharaohs like Hatshepsut and Ramesses II, building grand temples at Karnak and the tomb of Tutankhamun.",
            "imageQuery": "Tutankhamun gold mask",
        },
        {
            "title": "Late Period",
            "period": "664-332 BCE",
            "summary": "Egypt faced waves of foreign rule by Assyrians and Persians, with brief native revivals. Ancient traditions persisted amid growing outside pressure.",
            "imageQuery": "Temple of Philae",
        },
        {
            "title": "Greco-Roman Egypt",
            "period": "332 BCE-395 CE",
            "summary": "Alexander the Great founded Alexandria and the Ptolemaic dynasty, which ended with Cleopatra VII. Egypt then became a wealthy grain province of Rome.",
            "imageQuery": "Library of Alexandria",
        },
        {
            "title": "Islamic Egypt",
            "period": "641-1517 CE",
            "summary": "Arab armies brought Islam and Arabic to Egypt. Cairo grew into a major center of Islamic learning and power under the Fatimid, Ayyubid, and Mamluk rulers.",
            "imageQuery": "Al-Azhar Mosque Cairo",
        },
        {
            "title": "Ottoman & Muhammad Ali Era",
            "period": "1517-1882 CE",
            "summary": "Egypt became an Ottoman province, later modernized by Muhammad Ali Pasha's dynasty. The Suez Canal opened in 1869, reshaping global trade.",
            "imageQuery": "Suez Canal 1869",
        },
        {
            "title": "Modern Republic",
            "period": "1952-present",
            "summary": "The 1952 revolution ended the monarchy and created a republic under Nasser, who nationalized the Suez Canal. Egypt remains a leading power in the Arab world.",
            "imageQuery": "Cairo modern skyline",
        },
    ],
}
