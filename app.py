# File Organizer Pro — Phase 3 (Full, Fixed)
# Save this file as `app.py` and run with: streamlit run app.py

import os
import shutil
import zipfile
import hashlib
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from collections import Counter
import io

# -------------------------------------
# Configuration
# -------------------------------------
APP_TITLE = "File Organizer Pro — Phase 3 (Full)"
# Use a workspace inside the project directory so the app persists while running locally
WORKSPACE = Path.cwd() / "tmp_workspace"
CONFIG_FILE = Path.cwd() / "organizer_config.json"

# Default keyword rules for simple content-based categorization
DEFAULT_KEYWORD_RULES = {
    "Invoices": ["invoice", "bill", "amount due", "invoice no", "tax"],
    "Resumes": ["resume", "cv", "curriculum vitae"],
    "Research": ["abstract", "introduction", "method", "results", "conclusion"],
    "Screenshots": ["screenshot", "screen_shot"],
}

# Default extension->folder map
DEFAULT_CUSTOM_RULES = {
    "pdf": "Documents",
    "jpg": "Images",
    "jpeg": "Images",
    "png": "Images",
    "mp4": "Videos",
    "mp3": "Music",
}

# File type mapping used as fallback
FILE_TYPE_MAP = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'],
    'documents': ['.pdf', '.docx', '.doc', '.txt', '.pptx', '.xlsx', '.csv'],
    'videos': ['.mp4', '.mov', '.mkv', '.avi', '.flv'],
    'music': ['.mp3', '.wav', '.flac', '.aac'],
    'archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
}

# Ensure workspace exists
WORKSPACE.mkdir(parents=True, exist_ok=True)
(WORKSPACE / "extracted").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "organized").mkdir(parents=True, exist_ok=True)

# -------------------------------------
# Utility functions
# -------------------------------------

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def sha256_of_file(path: Path, block_size=65536) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(block_size), b''):
            h.update(blk)
    return h.hexdigest()


def normalize_path_str(p: str) -> str:
    """Normalize path string to use forward slashes and strip whitespace."""
    if not isinstance(p, str):
        return p
    return p.replace('\\', '/').strip()


def to_abs_path(p: str) -> Path:
    """Return an absolute Path inside WORKSPACE if given path is relative."""
    p = normalize_path_str(p)
    p_obj = Path(p)
    if not p_obj.is_absolute():
        return (WORKSPACE / p_obj).resolve()
    return p_obj.resolve()


def get_size_kb(path: Path):
    try:
        return round(os.path.getsize(path) / 1024, 2)
    except Exception:
        return None


def get_modified_iso(path: Path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def size_category(bytes_size: int):
    if bytes_size < 1_000_000:
        return "Small (<1MB)"
    elif bytes_size < 100_000_000:
        return "Medium (1MB-100MB)"
    else:
        return "Large (>100MB)"


def apply_rename_template(template: str, filepath: str, filehash: str) -> str:
    p = Path(filepath)
    name = p.stem
    ext = p.suffix.lstrip('.')
    try:
        date = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y%m%d")
    except Exception:
        date = datetime.utcnow().strftime("%Y%m%d")
    hash6 = (filehash or '')[:6]
    out = template.format(name=name, ext=ext, date=date, hash6=hash6)
    # if user didn't include ext in template, ensure extension appended
    if '{ext}' in template:
        return out
    else:
        if out.endswith(f'.{ext}'):
            return out
        return f"{out}.{ext}"


def ensure_unique(dst_path: Path) -> Path:
    if not dst_path.exists():
        return dst_path
    stem = dst_path.stem
    suffix = dst_path.suffix
    parent = dst_path.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def remove_empty_dirs(root_dir: Path):
    removed = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        if not dirnames and not filenames:
            try:
                os.rmdir(dirpath)
                removed.append(dirpath)
            except Exception:
                pass
    return removed

# -------------------------------------
# Streamlit initialization
# -------------------------------------
st.set_page_config(page_title=APP_TITLE, page_icon='📁', layout='wide')
st.title(APP_TITLE)
st.write("Advanced file organizer with content-based categorization, analytics, duplicates, previews, undo, and scheduler hints.")

# session state defaults
if 'history_stack' not in st.session_state:
    st.session_state.history_stack = []
if 'last_log_df' not in st.session_state:
    st.session_state.last_log_df = pd.DataFrame()
if 'duplicates' not in st.session_state:
    st.session_state.duplicates = pd.DataFrame()
if 'config' not in st.session_state:
    cfg = load_config()
    st.session_state.config = {
        'keyword_rules': cfg.get('keyword_rules', DEFAULT_KEYWORD_RULES),
        'custom_rules': cfg.get('custom_rules', DEFAULT_CUSTOM_RULES),
        'rename_template': cfg.get('rename_template', '{name}_{date}.{ext}')
    }

# -------------------------------------
# Sidebar: options and rules
# -------------------------------------
st.sidebar.header('⚙️ Options')
by_type = st.sidebar.checkbox('By File Type (extension)', True)
by_date = st.sidebar.checkbox('By Date Modified (YYYY-MM)', False)
by_size = st.sidebar.checkbox('By File Size Category', False)
custom_rules_toggle = st.sidebar.checkbox('Enable Custom Extension Rules', True)

st.sidebar.markdown('### 🔎 Content-based (AI-like) categorization')
use_keyword_categorizer = st.sidebar.checkbox('Enable keyword categorizer', True)
st.sidebar.caption('Lightweight content classifier using keyword matching — no external API required.')

st.sidebar.subheader('Keyword rules (Category:comma-separated keywords)')
kw_json = st.session_state.config.get('keyword_rules', DEFAULT_KEYWORD_RULES)
kw_text = '\n'.join([f"{cat}:{','.join(words)}" for cat, words in kw_json.items()])
kw_text_in = st.sidebar.text_area("Edit keyword rules (one per line 'Category:kw1,kw2')", value=kw_text, height=150)
# parse rules back
parsed_rules = {}
for line in kw_text_in.strip().splitlines():
    if ':' in line:
        cat, kws = line.split(':', 1)
        kws_list = [k.strip().lower() for k in kws.split(',') if k.strip()]
        if cat.strip():
            parsed_rules[cat.strip()] = kws_list
st.session_state.config['keyword_rules'] = parsed_rules or kw_json

st.sidebar.subheader('Custom extension -> Folder rules (ext:Folder, comma separated)')
custom_text = ','.join([f"{k}:{v}" for k, v in st.session_state.config.get('custom_rules', DEFAULT_CUSTOM_RULES).items()])
custom_text_in = st.sidebar.text_area('e.g. pdf:Documents, jpg:Images', value=custom_text, height=80)
parsed_custom = {}
for pair in custom_text_in.split(','):
    if ':' in pair:
        k, v = pair.split(':', 1)
        parsed_custom[k.strip().lower()] = v.strip()
st.session_state.config['custom_rules'] = parsed_custom or st.session_state.config.get('custom_rules', DEFAULT_CUSTOM_RULES)

st.sidebar.subheader('Rename template')
use_rename = st.sidebar.checkbox('Enable rename template', False)
rename_template = st.sidebar.text_input('Template (use {name}, {ext}, {date}, {hash6})', value=st.session_state.config.get('rename_template'))
st.session_state.config['rename_template'] = rename_template

st.sidebar.subheader('Duplicates / Cleanup')
detect_duplicates = st.sidebar.checkbox('Detect duplicates (SHA256)', True)
duplicate_action = st.sidebar.selectbox('If duplicates:', ['List only', 'Move duplicates to organized/Duplicates/', 'Delete duplicates (manual confirm)'])
cleanup_empty = st.sidebar.checkbox('Remove empty folders after organizing', True)

if st.sidebar.button('💾 Save rules & settings'):
    save_config(st.session_state.config)
    st.sidebar.success('Saved config to organizer_config.json')

# -------------------------------------
# Upload and workspace setup
# -------------------------------------
st.header('1) Upload ZIP folder to organize')
uploaded_zip = st.file_uploader('Upload ZIP containing folder(s)', type=['zip'])

if uploaded_zip:
    st.success('ZIP uploaded — workspace prepared.')
    # reset workspace
    if WORKSPACE.exists():
        try:
            shutil.rmtree(WORKSPACE)
        except Exception:
            pass
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / 'extracted').mkdir(parents=True, exist_ok=True)
    (WORKSPACE / 'organized').mkdir(parents=True, exist_ok=True)

    zip_path = WORKSPACE / 'uploaded.zip'
    with open(zip_path, 'wb') as f:
        f.write(uploaded_zip.read())

    extract_dir = WORKSPACE / 'extracted'
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(path=extract_dir)

    st.info(f'Extracted to `{extract_dir}`')

    organized_dir = WORKSPACE / 'organized'
    organized_dir.mkdir(parents=True, exist_ok=True)

    st.markdown('---')
    st.header('2) Run Organizer Now (one-off run)')

    if st.button('🪄 Organize Now (Smart + Content)'):
        files = [p for p in extract_dir.rglob('*') if p.is_file()]
        total = len(files)
        st.info(f'Found {total} files — processing...')
        progress = st.progress(0)
        moves = []
        log_rows = []
        sha_records = []

        for idx, p in enumerate(files, start=1):
            try:
                ext = p.suffix.lower()
                # decide destination folder: custom rules -> content -> type -> Others
                dest_folder = None
                if custom_rules_toggle and ext.lstrip('.') in st.session_state.config['custom_rules']:
                    dest_folder = organized_dir / st.session_state.config['custom_rules'][ext.lstrip('.')]
                else:
                    chosen_via_content = None
                    if use_keyword_categorizer:
                        sample = ''
                        if ext in ['.txt', '.md', '.csv', '.py', '.log', '.json']:
                            try:
                                sample = p.read_text(encoding='utf-8', errors='ignore').lower()[:5000]
                            except Exception:
                                sample = ''
                        # pdf parsing skipped in default
                        if sample:
                            for cat, kws in st.session_state.config['keyword_rules'].items():
                                for kw in kws:
                                    if kw and kw.lower() in sample:
                                        chosen_via_content = cat
                                        break
                                if chosen_via_content:
                                    break
                    if chosen_via_content:
                        dest_folder = organized_dir / chosen_via_content
                    else:
                        matched = False
                        for cat, exts in FILE_TYPE_MAP.items():
                            if ext in exts:
                                dest_folder = organized_dir / cat.capitalize()
                                matched = True
                                break
                        if not matched:
                            dest_folder = organized_dir / 'Others'

                # by_date / by_size
                if by_date:
                    mod_iso = datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m')
                    dest_folder = dest_folder / mod_iso
                if by_size:
                    dest_folder = dest_folder / size_category(p.stat().st_size)

                dest_folder.mkdir(parents=True, exist_ok=True)

                # compute hash if needed
                filehash = None
                if detect_duplicates or ('{hash6}' in rename_template):
                    try:
                        filehash = sha256_of_file(p)
                    except Exception:
                        filehash = ''

                # rename if enabled
                target_name = p.name
                if use_rename:
                    target_name = apply_rename_template(rename_template, str(p), filehash)

                target_path = ensure_unique(dest_folder / target_name)
                shutil.move(str(p), str(target_path))
                moves.append({'src': str(p), 'dst': str(target_path)})
                sha_records.append({'SHA256': filehash or '', 'File': target_path.name, 'Path': str(target_path), 'Size (KB)': get_size_kb(target_path)})
                log_rows.append([target_path.name, str(p), str(target_path), get_size_kb(target_path), get_modified_iso(target_path), filehash or ''])

            except Exception as e:
                st.error(f'Error processing {p}: {e}')

            progress.progress(int(idx/total*100) if total else 100)

        # save history and log
        st.session_state.history_stack.append(moves)
        log_df = pd.DataFrame(log_rows, columns=['File','Old Path','New Path','Size (KB)','Modified','SHA256'])
        st.session_state.last_log_df = log_df

        # duplicates
        dup_df = pd.DataFrame(sha_records)
        if not dup_df.empty:
            grouped = dup_df.groupby('SHA256').filter(lambda g: len(g) > 1)
            st.session_state.duplicates = grouped if not grouped.empty else pd.DataFrame(columns=dup_df.columns)
        else:
            st.session_state.duplicates = pd.DataFrame(columns=dup_df.columns)

        st.success(f'Finished organizing {len(log_rows)} files.')
        if cleanup_empty:
            removed = remove_empty_dirs(extract_dir)
            if removed:
                st.info(f'Removed {len(removed)} empty folders from extracted area.')

        # duplicate action handling
        if detect_duplicates and not st.session_state.duplicates.empty:
            st.warning(f'Found duplicate file groups: {st.session_state.duplicates['SHA256'].nunique()}')
            if duplicate_action == 'Move duplicates to organized/Duplicates/':
                dup_dir = organized_dir / 'Duplicates'
                dup_dir.mkdir(exist_ok=True)
                moved_count = 0
                for h, group in st.session_state.duplicates.groupby('SHA256'):
                    recs = group.sort_values('Path').to_dict('records')
                    for rec in recs[1:]:
                        srcp = Path(rec['Path'])
                        if srcp.exists():
                            tgt = ensure_unique(dup_dir / srcp.name)
                            shutil.move(str(srcp), str(tgt))
                            moved_count += 1
                st.info(f'Moved {moved_count} duplicate files to {dup_dir}')
            elif duplicate_action == 'Delete duplicates (manual confirm)':
                st.info('You selected delete — please carefully review duplicates table below and delete manually if desired.')

        st.balloons()

    # ---------------------------
    # Dashboard & Results
    # ---------------------------
    st.markdown('---')
    st.header('3) Dashboard & Results')
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Organize Log (last run)')
        if not st.session_state.last_log_df.empty:
            st.dataframe(st.session_state.last_log_df)
            csv = st.session_state.last_log_df.to_csv(index=False)
            st.download_button('📥 Download Log CSV', csv, 'organization_log.csv', 'text/csv')
        else:
            st.info('No run logged in this session yet.')

    with col2:
        st.subheader('Duplicates (if detected)')
        if not st.session_state.duplicates.empty:
            for h, group in st.session_state.duplicates.groupby('SHA256'):
                st.markdown(f"**Hash:** `{h}` — {len(group)} files")
                st.table(group[['File','Path','Size (KB)']])
                st.write('---')
        else:
            st.info('No duplicates found or detection disabled.')

    # analytics
    st.markdown('### Analytics')
    if not st.session_state.last_log_df.empty:
        def extract_top_folder(pathstr):
            parts = Path(pathstr).parts
            try:
                if 'organized' in parts:
                    i = parts.index('organized')
                    return parts[i+1] if len(parts) > i+1 else 'Unknown'
                else:
                    return parts[0] if parts else 'Unknown'
            except Exception:
                return 'Unknown'

        st.session_state.last_log_df['TopFolder'] = st.session_state.last_log_df['New Path'].apply(lambda x: extract_top_folder(x))
        dist = st.session_state.last_log_df['TopFolder'].value_counts()
        st.bar_chart(dist)

        st.write('File size distribution (KB)')
        st.hist_data = st.session_state.last_log_df['Size (KB)']
        size_bins = pd.cut(st.hist_data, bins=[0,1,10,100,1000,10000,100000])
        bin_counts = size_bins.value_counts().sort_index()
        bin_counts.index = bin_counts.index.astype(str)
        st.bar_chart(bin_counts)

        st.write('Top 10 largest files')
        topn = st.session_state.last_log_df.sort_values('Size (KB)', ascending=False).head(10)
        st.table(topn[['File','Size (KB)','New Path']])
    else:
        st.info('No analytics available until you run organize.')

# ---------------------------
# Preview / Manual Actions (Enhanced + Refresh Support) - FIXED
# ---------------------------
st.markdown('---')
st.header('4) Preview & Manual Actions')

# Refresh file list manually
if 'last_log_df' in st.session_state and not st.session_state.last_log_df.empty:
    if st.button('🔄 Refresh File List'):
        try:
            valid_paths = [p for p in st.session_state.last_log_df['New Path'].tolist() if Path(p).exists()]
            refreshed_df = st.session_state.last_log_df[st.session_state.last_log_df['New Path'].isin(valid_paths)]
            st.session_state.last_log_df = refreshed_df.reset_index(drop=True)
            st.success('✅ File list refreshed successfully!')
        except Exception as e:
            st.error(f'❌ Refresh failed: {e}')

    if not st.session_state.last_log_df.empty:
        preview_choice = st.selectbox(
            'Choose a file to preview or download',
            st.session_state.last_log_df['New Path'].tolist()
        )

        if preview_choice:
            # Normalize and use absolute path relative to workspace if needed
            preview_choice = normalize_path_str(preview_choice)
            p = Path(preview_choice)
            if not p.is_absolute():
                p = (WORKSPACE / p).resolve()

            st.write(f"**Path:** `{p}`")
            size = get_size_kb(p)

            if size is None or not p.exists():
                st.error('⚠️ File not found. It may have been moved or deleted.')
            else:
                st.write(f"**Size:** {size} KB")
                st.write(f"**Modified:** {get_modified_iso(p)}")

                try:
                    if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']:
                        st.image(str(p), caption=p.name, use_column_width=True)
                    elif p.suffix.lower() in ['.txt', '.py', '.md', '.csv', '.log', '.json']:
                        with open(p, 'r', errors='ignore') as fh:
                            snippet = ''.join([line for _, line in zip(range(30), fh)])
                        st.code(snippet)
                    elif p.suffix.lower() == '.pdf':
                        with open(p, 'rb') as fh:
                            st.download_button('📄 Download PDF', fh, file_name=p.name)
                    elif p.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']:
                        with open(p, 'rb') as fh:
                            st.video(fh.read())
                    else:
                        with open(p, 'rb') as fh:
                            st.download_button('⬇️ Download file', fh, file_name=p.name, mime='application/octet-stream')
                except Exception as e:
                    st.error(f'❌ Preview error: {e}')

                # Manual Move / Delete
                st.subheader('Manual Move / Delete')
                dest_manual = st.text_input('Manual destination path (absolute or relative) — leave blank to cancel', value=str(p.parent))

                col1, col2 = st.columns(2)
                with col1:
                    if st.button('🚚 Execute Manual Move'):
                        try:
                            os.makedirs(dest_manual, exist_ok=True)
                            tgt = ensure_unique(Path(dest_manual) / p.name)
                            shutil.move(str(p), str(tgt))
                            st.success(f'✅ Moved to {tgt}')
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f'❌ Error moving file: {e}')

                with col2:
                    if st.button('🗑️ Delete this file'):
                        try:
                            os.remove(p)
                            st.warning(f'🗑️ Deleted {p.name}')
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f'❌ Delete error: {e}')

else:
    st.info('ℹ️ Run organize to enable preview & manual actions.')

# ---------------------------
# Undo whole last organize
# ---------------------------
st.markdown('---')
st.header('5) Undo / Restore')
if st.button('↩️ Undo last organize operation (restore moved files)'):
    if not st.session_state.history_stack:
        st.info('Nothing to undo.')
    else:
        last_moves = st.session_state.history_stack.pop()
        errors = []
        for mv in reversed(last_moves):
            try:
                src = Path(mv['src'])
                dst = Path(mv['dst'])
                if dst.exists():
                    os.makedirs(src.parent, exist_ok=True)
                    shutil.move(str(dst), str(src))
                else:
                    errors.append(f'Missing dst {dst}')
            except Exception as e:
                errors.append(str(e))
        if not errors:
            st.success('Undo completed. Files restored.')
            st.session_state.last_log_df = pd.DataFrame()
            st.session_state.duplicates = pd.DataFrame()
        else:
            st.error('Some errors occurred during undo: ' + '; '.join(errors))

# ---------------------------
# Workspace actions: download zip, clear workspace
# ---------------------------
st.markdown('---')
st.header('6) Finalize / Download / Schedule')

if (WORKSPACE / 'organized').exists():
    if st.button('📦 Download organized folder as ZIP'):
        zip_name = 'organized_output.zip'
        zip_path = WORKSPACE / zip_name
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(WORKSPACE / 'organized'):
                for file in files:
                    absfile = os.path.join(root, file)
                    rel = os.path.relpath(absfile, WORKSPACE / 'organized')
                    zf.write(absfile, rel)
        with open(zip_path, 'rb') as fh:
            st.download_button('⬇️ Download ZIP', fh, file_name=zip_name, mime='application/zip')

    if st.button('🧹 Delete workspace (clear temp files)'):
        try:
            shutil.rmtree(WORKSPACE)
            st.success('Workspace deleted successfully.')
            st.session_state.last_log_df = pd.DataFrame()
            st.session_state.history_stack = []
            st.session_state.duplicates = pd.DataFrame()
        except Exception as e:
            st.error(f'Error deleting workspace: {e}')

    st.markdown('### Scheduling / Auto-run helpers')
    st.info(
        'This app cannot run in the background when closed. '
        'To auto-run regularly, use your OS scheduler:\n\n'
        '- **Windows**: Use Task Scheduler to run\n'
        '  `python -m streamlit run path\\to\\app.py --server.port 8501`\n\n'
        '- **macOS / Linux**: Use `cron` or `launchd` to run a small wrapper script that executes the organizer CLI.\n\n'
        'Alternatively, run this Streamlit app and click **Organize Now** whenever you want a manual run.'
    )

else:
    st.info(
        '📂 Upload a ZIP to begin.\n\n'
        '💡 Tip: zip your Downloads or target folder and upload here.\n\n'
        '⚙️ Running locally gives full file operations (manual move/delete).'
    )

# ---------------------------
# End of app
# ---------------------------
