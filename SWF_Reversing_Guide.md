# **SWF Reverse Engineering & Rebuilding Guide (1:1 Clone)**

## **Introduction**
This guide provides a step-by-step method to **reverse-engineer, extract, decrypt, and rebuild** SWF files **with 100% accuracy** while preserving all encrypted data, assets, and tag structures.

This method ensures:
- **1:1 Extraction & Decryption**
- **Full Asset Recovery**
- **Proper Encryption for Rebuilding**
- **Verification with Hashing to Ensure 100% Match**

---

## **1. Setup the Tools**
### **Requirements**
- Python 3.10+
- Dependencies: `pip install -r requirements.txt`
- Tools Required:
  - `swf_tag_extractor.py`
  - `decryption_routines.py`
  - `abc_processor.py`
  - `analyze_tags.py`
  - `rebuild_pipeline.py`

### **Directory Structure**
Ensure the following folders exist:
```
/robobuilder
 ├── tools/
 │    ├── extracted_tags/
 │    ├── rebuild_workspace/
 │    ├── analysis_output/
 │    ├── tag_analysis/
 │    ├── decrypted_tags/
```

---

## **2. Extract SWF Tags & Assets**
Run the extractor tool to pull all SWF tags into separate binary files.

```sh
python swf_tag_extractor.py --input EvonyClient1921.swf --output extracted_tags
```
Expected Output:
```
Extracted 3 tags of type 233 (Special Data Tag)
Extracted 4 tags of type 449 (Multi-Layer Tag)
Extracted 2 tags of type 82 (DoABC Tag)
```
---

## **3. Decrypt Encrypted SWF Tags**
Now decrypt special encrypted tags (233, 396, 449).

```sh
python decryption_routines.py analyze --tag-dir extracted_tags --tag-type 233
python decryption_routines.py analyze --tag-dir extracted_tags --tag-type 449
```
Expected Output:
```
Tag 233 decrypted successfully.
Tag 449 multi-layer decryption successful.
```

### **Manual Verification**
Check decrypted outputs:
```sh
ls decrypted_tags
```

---

## **4. Extract & Analyze ABC (ActionScript) Tags**
```sh
python abc_processor.py --input extracted_tags/82
```
Expected Output:
```
Processed ABC tag: version 1.68
Extracted ActionScript class structure.
```

---

## **5. Validate Hash Integrity (Before & After)**
Before rebuilding, compare original vs. extracted SWF:

```sh
python -c "import hashlib; print('Original:', hashlib.sha256(open('EvonyClient1921.swf', 'rb').read()).hexdigest()); print('Extracted:', hashlib.sha256(open('rebuilt.swf', 'rb').read()).hexdigest())"
```
If hashes **do not match**, further work is required.

---

## **6. Rebuild SWF (1:1 Accurate Clone)**
Once decryption is complete, rebuild the SWF file:
```sh
python rebuild_pipeline.py
```
Expected Output:
```
Rebuild completed successfully.
Final output: rebuild_workspace/final/rebuilt.swf
```

---

## **7. Final Verification & Testing**
Run hash comparison again:
```sh
python -c "import hashlib; print('Original:', hashlib.sha256(open('EvonyClient1921.swf', 'rb').read()).hexdigest()); print('Rebuilt:', hashlib.sha256(open('rebuilt.swf', 'rb').read()).hexdigest())"
```
If they **match 100%**, the rebuilding process was **successful**.

---

## **8. Debugging & Fixing Mismatches**
If the hashes do **not** match:
- Re-run decryption and check if all assets are correctly extracted.
- Ensure encryption keys match exactly.
- Check if padding bytes are preserved.
- Manually inspect `decrypted_tags/` for missing bytes.

---

## **Conclusion**
This guide ensures that the SWF file is **fully extracted, decrypted, and rebuilt correctly** into a **100% 1:1 clone**. Any deviation can be traced via hash mismatches, ensuring a perfect rebuild.

For additional debugging, re-run:
```sh
python analyze_tags.py
python decryption_routines.py
python abc_processor.py
```

Good luck! 🚀
