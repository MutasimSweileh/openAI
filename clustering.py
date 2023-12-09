import io
import pandas as pd
import sys
from polyfuzz import PolyFuzz
import chardet
from tqdm import tqdm
import os

parent_by_vol = True
drop_site_links = False
drop_image_links = False
sim_match_percent = 1
url_filter = ""
min_volume = 0  # set the minimum search volume / impressions to filter on

info_filter = "what|where|why|when|who|how|which|tip|guide|tutorial|ideas|example|learn|wiki|in mm|in cm|in ft|in feet"
comm_invest_filter = "best|vs|list|compare|review|list|top|difference between"
trans_filter = "purchase|bargain|cheap|deal|value|closeout|buy|shop|price|coupon|discount|price|pricing|delivery|shipping|order|returns|sale|amazon|target|ebay|walmart|cost of|how much"

# ---------------------------------- auto detect character encoding ----------------------------------------------------


def keyword_clustering(input_file):

    file_extension = os.path.splitext(input_file)
   # with open(input_file, 'rb') as rawdata:
    with open(input_file, 'rb') as rawdata:
        result = chardet.detect(rawdata.read(10000))
    # result = chardet.detect(input_file)
    # if the encoding is utf-16 use a space separator, else ','
    if result['encoding'] == "UTF-16":
        white_space = True
    else:
        white_space = False

    if (
        file_extension[1] == ".xlsx"
        or file_extension[1] == ".xls"
        or file_extension[1] == ".xlsm"
        or file_extension[1] == ".xlsb"
        or file_extension[1] == ".odf"
        or file_extension[1] == ".ods"
        or file_extension[1] == ".odt"
    ):
        df_1 = pd.read_excel(input_file, engine="openpyxl")
    else:
        try:
            df_1 = pd.read_csv(
                input_file,
                encoding=result["encoding"],
                delim_whitespace=white_space,
                on_bad_lines="skip",
            )
        # fall back to utf-8
        except UnicodeDecodeError:
            df_1 = pd.read_csv(
                input_file,
                encoding="utf-8",
                delim_whitespace=white_space,
                on_bad_lines="skip",
            )
    # -------------------------- check if single column import / and write header if missing -------------------------------

    # check the number of columns
    col_len = len(df_1.columns)
    col_name = df_1.columns[0]

    if col_len == 1 and df_1.columns[0] != "Keyword":
        df_1.columns = ["Keyword"]

    if col_len == 1 and df_1.columns[0] != "keyword":
        df_1.columns = ["Keyword"]
    # -------------------------- detect if import file is adwords and remove the first two rows ----------------------------
    adwords_check = False
    if col_name == "Search terms report":
        df_1.columns = df_1.iloc[1]
        df_1 = df_1[1:]
        df_1 = df_1.reset_index(drop=True)

        new_header = df_1.iloc[0]  # grab the first row for the header
        df_1 = df_1[1:]  # take the data less the header row
        df_1.columns = new_header  # set the header row as the df header
        adwords_check = True
    # --------------------------------- Check if csv data is gsc and set bool ----------------------------------------------

    if 'Impressions' in df_1.columns:
        gsc_data = True
    # ----------------- standardise the column names between ahrefs v1/v2/semrush/gsc keyword exports ----------------------

    df_1.rename(
        columns={
            "Current position": "Position",
            "Current URL": "URL",
            "Current URL inside": "Page URL inside",
            "Current traffic": "Traffic",
            "KD": "Difficulty",
            "Keyword Difficulty": "Difficulty",
            "Search Volume": "Volume",
            "page": "URL",
            "query": "Keyword",
            "Top queries": "Keyword",
            "Impressions": "Volume",
            "Clicks": "Traffic",
            "Search term": "Keyword",
            "Impr.": "Volume",
            "Search vol.": "Volume",
        },
        inplace=True,
    )
    # ------------------------------ check number of imported rows and warn if excessive -----------------------------------

    row_len = len(df_1)
    if col_len > 1:
        # --------------------------------- clean the data pre-grouping ----------------------------------------------------

        if url_filter:
            print("Processing only URLs containing:", url_filter)

        try:
            df_1 = df_1[df_1["URL"].str.contains(url_filter, na=False)]
        except KeyError:
            pass

        # ========================= clean strings out of numerical columns (adwords) ========================================

        try:
            df_1["Volume"] = df_1["Volume"].str.replace(",", "").astype(int)
            df_1["Traffic"] = df_1["Traffic"].str.replace(",", "").astype(int)
            df_1["Conv. value / click"] = df_1["Conv. value / click"].str.replace(
                ",", "").astype(float)
            df_1["All conv. value"] = df_1["All conv. value"].str.replace(
                ",", "").astype(float)
            df_1["CTR"] = df_1["CTR"].replace(" --", "0", regex=True)
            df_1["CTR"] = df_1["CTR"].str.replace("\%", "").astype(float)
            df_1["Cost"] = df_1["Cost"].astype(float)
            df_1["Conversions"] = df_1["Conversions"].astype(int)
            df_1["Cost"] = df_1["Cost"].round(2)
            df_1["All conv. value"] = df_1["All conv. value"].astype(float)
            df_1["All conv. value"] = df_1["All conv. value"].round(2)

        except Exception:
            pass

        df_1 = df_1[~df_1["Keyword"].str.contains(
            "Total: ", na=False)]  # remove totals rows
        df_1 = df_1[df_1["Keyword"].notna()]  # keep only rows which are NaN
        df_1 = df_1[df_1["Volume"].notna()]  # keep only rows which are NaN
        df_1["Volume"] = df_1["Volume"].astype(str)
        df_1["Volume"] = df_1["Volume"].apply(lambda x: x.replace("0-10", "0"))
        df_1["Volume"] = df_1["Volume"].astype(float).astype(int)

        # drop sitelinks

        if drop_site_links:
            try:
                df_1 = df_1[~df_1["Page URL inside"].str.contains(
                    "Sitelinks", na=False)]  # drop sitelinks
            except KeyError:
                pass
            try:
                if gsc_data:
                    df_1 = df_1.sort_values(by="Traffic", ascending=False)
                    df_1.drop_duplicates(
                        subset="Keyword", keep="first", inplace=True)
            except NameError:
                pass

        if drop_image_links:
            try:
                df_1 = df_1[~df_1["Page URL inside"].str.contains(
                    "Image pack", na=False)]  # drop image pack
            except KeyError:
                pass

        df_1 = df_1[df_1["Volume"] > min_volume]

    # start strip out all special characters from a column
    spec_chars = ["!", '"', "#", "%", "'", "(", ")",
                  "*", "+", ",", "-", ".", "/", ":", ";", "<",
                  "=", ">", "?", "@", "[", "\\", "]", "^", "_",
                  "`", "{", "|", "}", "~", "–"]
    for char in spec_chars:
        df_1['Keyword'] = df_1['Keyword'].str.replace(char, ' ')
    # ------------------------------------- do the grouping ----------------------------------------------------------------

    df_1_list = df_1.Keyword.tolist()  # create list from df
    model = PolyFuzz("TF-IDF")

    cluster_tags = df_1_list[::]
    cluster_tags = set(cluster_tags)
    cluster_tags = list(cluster_tags)

    print("Cleaning up the cluster tags.. Please be patient!")
    substrings = {w1 for w1 in tqdm(cluster_tags)
                  for w2 in cluster_tags if w1 in w2 and w1 != w2}
    longest_word = set(cluster_tags) - substrings
    longest_word = list(longest_word)
    shortest_word_list = list(set(cluster_tags) - set(longest_word))

    try:
        model.match(df_1_list, shortest_word_list)
    except ValueError:
        print("Empty Dataframe, Can't Match - Check the URL Filter!")
        sys.exit()

    model.group(link_min_similarity=sim_match_percent)
    df_matched = model.get_matches()
    # ------------------------------- clean the data post-grouping ---------------------------------------------------------

    # renaming multiple columns
    df_matched.rename(columns={"From": "Keyword",
                               "Group": "Cluster Name"}, inplace=True)

    # merge keyword volume / CPC / Pos / URL etc data from original dataframe back in
    df_matched = pd.merge(df_matched, df_1, on="Keyword", how="left")

    # rename traffic (acs) / (desc) to 'Traffic for standardisation
    df_matched.rename(columns={"Traffic (desc)": "Traffic",
                               "Traffic (asc)": "Traffic", "Traffic potential": "Traffic"}, inplace=True)

    if col_len > 1:

        # fill in missing values
        df_matched.fillna({"Traffic": 0, "CPC": 0}, inplace=True)
        # print(df_matched)
        df_matched['Traffic'] = 0
        df_matched['Traffic'] = df_matched['Traffic'].round(0)
        # ------------------------- group the data and merge in original stats -------------------------------------------------
        if not adwords_check:
            try:
                # make dedicated grouped dataframe
                df_grouped = (df_matched.groupby("Cluster Name").agg(
                    {"Volume": sum, "Difficulty": "median", "CPC": "median", "Traffic": sum}).reset_index())
            except Exception:
                df_grouped = (df_matched.groupby("Cluster Name").agg(
                    {"Volume": sum, "Traffic": sum}).reset_index())

            df_grouped = df_grouped.rename(
                columns={"Volume": "Cluster Volume", "Difficulty": "Cluster KD (Median)", "CPC": "Cluster CPC (Median)",
                         "Traffic": "Cluster Traffic"})

            # merge in the group stats
            df_matched = pd.merge(df_matched, df_grouped,
                                  on="Cluster Name", how="left")

        if adwords_check:

            df_grouped = (df_matched.groupby("Cluster Name").agg(
                {"Volume": sum, "CTR": "median", "Cost": sum, "Traffic": sum, "All conv. value": sum, "Conversions": sum}).reset_index())

            df_grouped = df_grouped.rename(
                columns={"Volume": "Cluster Volume", "CTR": "Cluster CTR (Median)", "Cost": "Cluster Cost (Sum)",
                         "Traffic": "Cluster Traffic", "All conv. value": "All conv. value (Sum)", "Conversions": "Cluster Conversions (Sum)"})

            # merge in the group stats
            df_matched = pd.merge(df_matched, df_grouped,
                                  on="Cluster Name", how="left")

            del df_matched['To']
            del df_matched['Similarity']

        # ---------------------------- clean and sort the final output -----------------------------------------------------

        try:
            # drop if both kw & url are duped
            df_matched.drop_duplicates(
                subset=["URL", "Keyword"], keep="first", inplace=True)
        except KeyError:
            pass
    if not adwords_check:
        cols = (
            "Cluster Name",
            "Keyword",
            "Cluster Size",
            "Cluster Volume",
            "Cluster KD (Median)",
            "Cluster CPC (Median)",
            "Cluster Traffic",
            "Volume",
            "Difficulty",
            "CPC",
            "Traffic",
            "URL",
        )

        df_matched = df_matched.reindex(columns=cols)

        try:
            if gsc_data:
                cols = "Cluster Name", "Keyword", "Cluster Size", "Cluster Volume", "Cluster Traffic", "Volume", "Traffic"
                df_matched = df_matched.reindex(columns=cols)
        except NameError:
            pass
    # ------------ get the keyword with the highest search volume to replace the auto generated tag name with --------------

    if col_len > 1:
        if parent_by_vol:
            df_matched['vol_max'] = df_matched.groupby(
                ['Cluster Name'])['Volume'].transform(max)
            # this sort is mandatory for the renaming to work properly by floating highest values to the top of the cluster
            df_matched.sort_values(["Cluster Name", "Cluster Volume", "Volume"], ascending=[
                False, True, False], inplace=True)
            df_matched['exact_vol_match'] = df_matched['vol_max'] == df_matched['Volume']
            df_matched.loc[df_matched['exact_vol_match'] == True,
                           'highest_ranked_keyword'] = df_matched['Keyword']
            df_matched['highest_ranked_keyword'] = df_matched['highest_ranked_keyword'].fillna(
                method='ffill')
            df_matched['Cluster Name'] = df_matched['highest_ranked_keyword']
            del df_matched['vol_max']
            del df_matched['exact_vol_match']
            del df_matched['highest_ranked_keyword']
    if adwords_check:
        df_matched = df_matched.rename(columns={
            "Volume": "Impressions", "Traffic": "Clicks", "Cluster Traffic": "Cluster Clicks (Sum)"})
    # -------------------------------------- final output ------------------------------------------------------------------
    # sort on cluster size
    df_matched.sort_values(["Cluster Size", "Cluster Name", "Cluster Volume"], ascending=[
        False, True, False], inplace=True)

    try:
        if gsc_data:
            df_matched.rename(
                columns={"Cluster Volume": "Cluster Impressions", "Cluster Traffic": "Cluster Clicks", "Traffic": "Clicks",
                         "Volume": "Impressions"}, inplace=True)
    except NameError:
        pass

    if col_len == 1:
        cols = "Cluster Name", "Keyword", "Cluster Size"
        df_matched = df_matched.reindex(columns=cols)
    # - add in intent markers
    colname = df_matched.columns[1]
    df_matched.loc[df_matched[colname].str.contains(
        info_filter), "Informational"] = "Informational"
    df_matched.loc[df_matched[colname].str.contains(
        comm_invest_filter), "Commercial Investigation"] = "Commercial Investigation"
    df_matched.loc[df_matched[colname].str.contains(
        trans_filter), "Transactional"] = "Transactional"
    # find keywords from one column in another in any order and count the frequency
    df_matched['Cluster Name'] = df_matched['Cluster Name'].str.strip()
    df_matched['Keyword'] = df_matched['Keyword'].str.strip()

    df_matched['First Word'] = df_matched['Cluster Name'].str.split(" ").str[0]
    df_matched['Second Word'] = df_matched['Cluster Name'].str.split(
        " ").str[1]
    df_matched['Total Keywords'] = df_matched['First Word'].str.count(' ') + 1

    def ismatch(s):
        A = set(s["First Word"].split())
        B = set(s['Keyword'].split())
        return A.intersection(B) == A

    df_matched['Found'] = df_matched.apply(ismatch, axis=1)

    df_matched = df_matched. fillna('')

    def ismatch(s):
        A = set(s["Second Word"].split())
        B = set(s['Keyword'].split())
        return A.intersection(B) == A

    df_matched['Found 2'] = df_matched.apply(ismatch, axis=1)

    # todo - document this algo. Essentially if it matches on the second word only, it renames the cluster to the second word
    # clean up code nd variable names

    df_matched.loc[(df_matched["Found"] == False) & (
        df_matched["Found 2"] == True), "Cluster Name"] = df_matched["Second Word"]
    df_matched.loc[(df_matched["Found"] == False) & (
        df_matched["Found 2"] == False), "Cluster Name"] = "zzz_no_cluster_available"

    # count cluster_size
    df_matched['Cluster Size'] = df_matched['Cluster Name'].map(
        df_matched.groupby('Cluster Name')['Cluster Name'].count())
    df_matched.loc[df_matched["Cluster Size"] == 1,
                   "Cluster Name"] = "zzz_no_cluster_available"

    df_matched = df_matched.sort_values(by="Cluster Name", ascending=True)

    # delete the helper cols
    del df_matched['First Word']
    del df_matched['Second Word']
    del df_matched['Total Keywords']
    del df_matched['Found']
    del df_matched['Found 2']
    u = []
    for i, k in enumerate(df_matched['Cluster Name']):
        if k not in u or k == "zzz_no_cluster_available":
            if k == "zzz_no_cluster_available":
                k = df_matched['Keyword'].get(i)
            u.append(k)
        # print(k)
    # print("\n".join(u))
    url = 'your_keywords_clustered.csv'
    df_matched.to_csv(url.strip("/"), index=False)
    return {
        "data": u,
        "url": url
    }


    # print(df_matched['Cluster Name'].all())
    # df_matched.to_csv('your_keywords_clustered.csv', index=False)
d = keyword_clustering("bike-helmet_broad-match_us_2023-05-29.csv")
print(d)
