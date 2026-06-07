# Risk: Repository Privacy

## Risk

Plaka, yüz, cabin, raw video veya evidence görüntüleri repoya yanlışlıkla commit edilebilir. Repo private olsa bile bu dosyalar Git geçmişinde kalıcı risk oluşturur.

## Impact

KVKK/etik risk ve güvenlik ihlali oluşur.

## Mitigation

* `.gitignore` medya, model artifact ve secret dosyalarını engeller.
* Commit öncesi `governance/security/public_repo_safety_checklist.md` uygulanır.
* Evidence medyası private/local storage altında tutulur.

## Status

Open.
