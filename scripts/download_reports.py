import os
import urllib.request
import hashlib

REPORTS = {
    "Samsung_Electronics_Sustainability_Report_2024_ENG.pdf": (
        "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/Samsung_Electronics_Sustainability_Report_2024_ENG.pdf",
        "7d1ebb916e76a93d4f9e8d3aed363b994a4c25d0cfc81dc83b7449ada1804c36"
    ),
    "skhynix_sustainability_report_archive.html": (
        "https://www.skhynix.com/sustainability/UI-FR-SA1601/",
        "cc3d60fa15f7daaf20dacc1f68ae2eb983240b15d992e37b1c2f140eca3d494a"
    ),
    "nssc_201_samsung_radiation.pdf": (
        "https://www.nssc.go.kr/attach/namo/files/000002/20240926174645693_1E891JFD.pdf",
        "f2c9bc122381908b1b5524f7259ed75b92f9e98f99717630e1ce486a5ea2dea8"
    ),
    "moel_19573_skhynix_fluorine_inspection.html": (
        "https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19573",
        "44fe001e0227990956b6d21a3181907d7c67d7b517f8124928ddf9dd61cfe618"
    ),
    "pipc_8994_samsung_privacy.html": (
        "https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&mCode=C020010000&nttId=8994",
        "df894e579cbee876084c0997683b6f35c8d0e708a22652751ab8f00248e0cd02"
    )
}

def main():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "reports")
    os.makedirs(target_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for filename, (url, expected_hash) in REPORTS.items():
        dest = os.path.join(target_dir, filename)
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                content = response.read()
            
            actual_hash = hashlib.sha256(content).hexdigest()
            print(f"  Calculated hash: {actual_hash}")
            print(f"  Expected hash:   {expected_hash}")
            
            with open(dest, "wb") as f:
                f.write(content)
            
            if actual_hash == expected_hash:
                print(f"  [+] Match success!")
            else:
                print(f"  [-] Hash mismatch! Writing anyway.")
        except Exception as e:
            print(f"  [-] Error downloading {filename}: {e}")

if __name__ == "__main__":
    main()
