import streamlit as st
import pandas as pd
import io
import re
from fuzzywuzzy import fuzz

# Streamlit app title
st.title("Enhanced Brand List Cleaner with Per-Flag Downloads")
st.write("Upload your Excel file with a 'Brand' column. This app will clean it by trimming whitespace, standardizing case, removing duplicates, empties, short names, pure numbers, special characters, number prefixes, generic names, numerical artifacts, spelling variants (including space-related variants), long brands with more than two spaces, and obvious generic terms. The summary is shown in an accordion format, with downloads for each flag's removed entries and the cleaned dataset.")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    st.write("**Original Data Preview:**")
    st.dataframe(df.head(10))
    
    # Assume brand column is 'Brand' – you can change this
    brand_col = 'Brand'
    if brand_col not in df.columns:
        st.error(f"Column '{brand_col}' not found. Available columns: {list(df.columns)}")
        st.stop()
    
    # Cleaning button
    if st.button("Clean Brands"):
        df_clean = df.copy()
        original_count = len(df_clean)
        
        # Track removals with descriptions and flagged data
        removals = {
            'empty_null': {'count': 0, 'description': 'Empty or null entries (e.g., "", "nan", "NaN").', 'data': []},
            'too_short': {'count': 0, 'description': 'Brands with 2 or fewer characters (e.g., "AA", "AB").', 'data': []},
            'pure_numbers': {'count': 0, 'description': 'Brands that are purely numeric (e.g., "123", "456").', 'data': []},
            'special_chars': {'count': 0, 'description': 'Brands containing special characters other than letters, spaces, or hyphens (e.g., "0+1", "2jeuxm“mes").', 'data': []},
            'number_prefix': {'count': 0, 'description': 'Brands starting with numbers (e.g., "123 Sesame Street", "0+1").', 'data': []},
            'generic_names': {'count': 0, 'description': 'Short, generic letter combinations (e.g., "AAA", "ABC").', 'data': []},
            'numerical_artifacts': {'count': 0, 'description': 'Brands that are numerical values with decimals (e.g., "0.833333333333333").', 'data': []},
            'spelling_variants': {'count': 0, 'description': 'Brands with similar spellings, including space variations (e.g., "Healthgarde", "Health Garde", "Health Garden").', 'data': []},
            'long_multi_space': {'count': 0, 'description': 'Brands with more than two spaces (e.g., "A B C D").', 'data': []},
            'obvious_generic': {'count': 0, 'description': 'Brands that are obvious generic terms (e.g., "Clothing", "Fashion").', 'data': []}
        }
        
        # Store variant groupings for display
        variant_groups = []
        
        # Convert to string and trim
        df_clean[brand_col] = df_clean[brand_col].astype(str).str.strip()
        
        # Remove empties/nulls
        mask_empty = df_clean[brand_col].isin(['', 'nan', 'NaN'])
        removals['empty_null']['count'] = mask_empty.sum()
        removals['empty_null']['data'] = df_clean[mask_empty][[brand_col]]
        df_clean = df_clean[~mask_empty]
        
        # Remove too short (≤2 chars to catch "AA", "AB", etc.)
        mask_short = df_clean[brand_col].str.len() <= 2
        removals['too_short']['count'] = mask_short.sum()
        removals['too_short']['data'] = df_clean[mask_short][[brand_col]]
        df_clean = df_clean[~mask_short]
        
        # Remove pure numbers
        mask_numbers = df_clean[brand_col].str.match(r'^\d+$')
        removals['pure_numbers']['count'] = mask_numbers.sum()
        removals['pure_numbers']['data'] = df_clean[mask_numbers][[brand_col]]
        df_clean = df_clean[~mask_numbers]
        
        # Remove special characters (keep only letters, spaces, and hyphens)
        mask_special = df_clean[brand_col].apply(lambda x: bool(re.search(r'[^a-zA-Z\s\-]', x)))
        removals['special_chars']['count'] = mask_special.sum()
        removals['special_chars']['data'] = df_clean[mask_special][[brand_col]]
        df_clean = df_clean[~mask_special]
        
        # Remove brands starting with numbers (e.g., "123 Sesame Street", "0+1")
        mask_number_prefix = df_clean[brand_col].str.match(r'^\d+[\s\S]*')
        removals['number_prefix']['count'] = mask_number_prefix.sum()
        removals['number_prefix']['data'] = df_clean[mask_number_prefix][[brand_col]]
        df_clean = df_clean[~mask_number_prefix]
        
        # Remove generic names (e.g., "AA", "AAA", "ABC")
        generic_patterns = r'^(AA|A\+A|AAA|AAAA|A\+|A\&A|A\sA|A\s\&\sA|AB|A\sB|AC|A\sC|ABC|A\sB\sC)$'
        mask_generic = df_clean[brand_col].str.match(generic_patterns, case=False)
        removals['generic_names']['count'] = mask_generic.sum()
        removals['generic_names']['data'] = df_clean[mask_generic][[brand_col]]
        df_clean = df_clean[~mask_generic]
        
        # Remove numerical artifacts (e.g., "0.833333333333333")
        mask_numerical = df_clean[brand_col].str.match(r'^\d*\.\d+$')
        removals['numerical_artifacts']['count'] = mask_numerical.sum()
        removals['numerical_artifacts']['data'] = df_clean[mask_numerical][[brand_col]]
        df_clean = df_clean[~mask_numerical]
        
        # Remove brands with more than two spaces (e.g., "A B C D")
        mask_multi_space = df_clean[brand_col].apply(lambda x: len(re.findall(r'\s+', x)) > 2)
        removals['long_multi_space']['count'] = mask_multi_space.sum()
        removals['long_multi_space']['data'] = df_clean[mask_multi_space][[brand_col]]
        df_clean = df_clean[~mask_multi_space]
        
        # Remove obvious generic terms (e.g., "Clothing", "Fashion")
        obvious_generic_terms = [
            'clothing', 'fashion', 'apparel', 'brand', 'style', 'wear', 'textile', 
            'garment', 'accessories', 'accessory', 'beauty', 'cosmetics', 'shoes', 
            'footwear', 'jewelry', 'jewellery', 'bags', 'handbags'
        ]
        mask_obvious = df_clean[brand_col].str.lower().isin(obvious_generic_terms)
        removals['obvious_generic']['count'] = mask_obvious.sum()
        removals['obvious_generic']['data'] = df_clean[mask_obvious][[brand_col]]
        df_clean = df_clean[~mask_obvious]
        
        # Standardize case for fuzzy matching
        df_clean[brand_col] = df_clean[brand_col].str.title()
        
        # Remove spelling variants using fuzzy matching with space normalization
        brands = df_clean[brand_col].tolist()
        keep_indices = []
        variant_indices = []
        similarity_threshold = 85  # Catches variants like "Healthgarde" and "Health Garden"
        
        for i in range(len(brands)):
            if i not in variant_indices:
                keep_indices.append(i)
                current_variants = [brands[i]]
                for j in range(i + 1, len(brands)):
                    if j not in variant_indices:
                        # Normalize spaces for comparison
                        norm_i = re.sub(r'\s+', '', brands[i].lower())
                        norm_j = re.sub(r'\s+', '', brands[j].lower())
                        similarity = fuzz.ratio(norm_i, norm_j)
                        if similarity >= similarity_threshold:
                            variant_indices.append(j)
                            removals['spelling_variants']['count'] += 1
                            current_variants.append(brands[j])
                if len(current_variants) > 1:
                    variant_groups.append(current_variants)
        # Store flagged variants data
        removals['spelling_variants']['data'] = df_clean.iloc[variant_indices][[brand_col]].reset_index(drop=True)
        
        # Keep only non-variant entries
        df_clean = df_clean.iloc[keep_indices].reset_index(drop=True)
        
        # Remove exact duplicates
        pre_dup_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=[brand_col])
        duplicates_removed = pre_dup_count - len(df_clean)
        
        final_count = len(df_clean)
        
        # Summary
        st.subheader("**Cleanup Summary**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Rows", original_count)
        with col2:
            st.metric("Final Unique Brands", final_count)
        with col3:
            st.metric("Total Removed", original_count - final_count)
        
        # Accordion for flagged/removed breakdown
        st.write("**Breakdown of Flagged/Removed:**")
        for reason, info in removals.items():
            with st.expander(f"{reason.replace('_', ' ').title()} ({info['count']} removed)"):
                st.write(f"- **Description**: {info['description']}")
                st.write(f"- **Count Removed**: {info['count']}")
                if not info['data'].empty:
                    st.write("**Flagged Entries:**")
                    st.dataframe(info['data'])
                    # Download button for flagged entries
                    output = io.BytesIO()
                    info['data'].to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    st.download_button(
                        label=f"Download {reason.replace('_', ' ').title()} Flagged Entries",
                        data=output.getvalue(),
                        file_name=f"flagged_{reason}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.write("No entries flagged for this category.")
        
        # Accordion for variant groupings
        if variant_groups:
            with st.expander("Detected Spelling Variant Groups"):
                st.write("The following groups of similar brand names were detected. The first entry in each group was kept, and others were flagged as variants:")
                for group in variant_groups:
                    st.write(f"- Kept: '{group[0]}', Flagged as Variants: {group[1:]}")
        
        st.write("**Cleaned Data Preview:**")
        st.dataframe(df_clean.head(10))
        
        # Download cleaned file
        output = io.BytesIO()
        df_clean.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.download_button(
            label="Download Cleaned Excel",
            data=output.getvalue(),
            file_name="cleaned_brands.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
