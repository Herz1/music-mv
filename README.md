# music-mv — 八木海莉「TINY LUCK」非公式ファンMV

映画『GROTESQQQUE-グロテスク-』劇中歌「TINY LUCK」（作詞：八木海莉／作曲・編曲：eba／歌：八木海莉）の
**非公式ファンMV**です。公式映像ではありません。

制作は [vocaloid-style-mv-pipeline](https://github.com/EGSECDA/vocaloid-style-mv-pipeline)（EGSECDA / NikusonP, MIT）の
skill ワークフローに沿っています（分析→概念→角色→分镜→时间线→渲染→审片→交付）。

## 成片（tiny-luck-mv/render/）
| ファイル | 仕様 |
|---|---|
| `TINY_LUCK_MV_16x9_v2.mp4` | 1280×720 / 24fps / 3:44.04（曲 3:41.04＋残像クレジット3s）/ H.264 CRF24 / AAC 256k |
| `TINY_LUCK_MV_9x16_v2.mp4` | 720×1280 / 24fps / 同尺 / ネイティブ竖版再レイアウト |

## 直播（v2、Range対応でシーク可）
- 观看页：`https://8000-iar05yj4v9me41gxxh7ad.e2b.app/`（本沙箱存活中のみ）
- 16:9：`https://8000-iar05yj4v9me41gxxh7ad.e2b.app/TINY_LUCK_MV_16x9_v2.mp4`
- 9:16：`https://8000-iar05yj4v9me41gxxh7ad.e2b.app/TINY_LUCK_MV_9x16_v2.mp4`

## 素材（ユーザー提供）
- 音源：`music - Converted with FlexClip.mp3`（本リポジトリ main にアップロードされたもの）
- 歌詞・日中対訳：`lyrics.md`（同上）

## プロジェクト構成（tiny-luck-mv/）
- `docs/` CONCEPT（概念）/ CHARACTER（角色设定）/ STORYBOARD（44镜分镜）/ AUDIO_MAP / QA
- `analysis/` audio.json（拍・小節・段落）/ lyrics_mv.lrc / lyrics_translation.json / overview.png
- `assets/` 背景3枚＋角色主图・姿势7枚（原图生成→品紅抠图 RGBA）
- `engine_py/` 決定的 Python レンダラー（timeline.py = 分镜実装、mv_engine.py、render.py）
- `tools_py/` analyze.py（拍/段落/歌詞タイミング推定）、key_assets.py（抠图）

## 再レンダリング
```bash
cd tiny-luck-mv
pip install numpy pillow scipy imageio-ffmpeg   # ffmpeg は imageio-ffmpeg 同梱バイナリを使用可
python tools_py/analyze.py
python tools_py/key_assets.py
python engine_py/render.py --mode stills --times 2,50,68,151 --outdir render/stills/check --sheet check
python engine_py/render.py --mode video --out render/TINY_LUCK_MV_16x9.mp4 --width 1280 --height 720 --crf 24 --preset fast
python engine_py/render.py --mode video --out render/TINY_LUCK_MV_9x16.mp4 --width 720 --height 1280 --crf 24 --preset fast --vertical
```

## 注意
- 歌詞タイミングは推定アライメント（±約1s、docs/AUDIO_MAP.md 参照）。
- 本MVの公開・再配布には原曲権利者の許諾が必要です。学習・制作検証目的のファンワークとして扱ってください。
