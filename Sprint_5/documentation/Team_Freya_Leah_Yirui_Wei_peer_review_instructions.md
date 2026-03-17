# Running the Service

## Run from the exported Docker image (.tar)

This is the method peer reviewers should use after downloading the exported Docker image.

### If you saved the files in your Downloads folder

``` bash
cd ~/Downloads
docker load -i Team_Freya_Leah_Yirui_Wei_Coleman_image.tar
docker run -p 8000:8000 interface-corpus-search:latest
```

Then open the following URL in your browser:

``` text
http://localhost:8000
```

------------------------------------------------------------------------

# What peer reviewers should try

Please test the following parts of the interface:

1.  Open the app in the browser using the URL and port listed above.
    -   Confirm that the landing page loads successfully.
2.  Test the landing page video.
    -   Verify that the hero video appears on the first page.
    -   Click the play/pause button in the lower-right corner and confirm that the video can be paused and resumed.
3.  Enter the corpus interface.
    -   Click **Explore the review corpus**.
    -   Confirm that the app transitions from the landing page to the main corpus search page.
4.  Run a basic keyword search.
    -   Enter a keyword in the search bar and click **Search**.
    -   Confirm that results are returned.
    -   Verify that each result shows a title, snippet, document ID, rating, and relevance score.
5.  Test search-field filtering.
    -   Run the same query using different search fields:
        -   all
        -   title
        -   description
        -   reviewText
    -   Check whether the returned results or rankings change appropriately.
6.  Test annotated-only mode.
    -   Check **Annotated data only**.
    -   Confirm that the attribute filter section becomes visible.
7.  Test attribute filtering.
    -   Select one or more attributes.
    -   Click **Apply Filters**.
    -   Confirm that the annotation results shown in each result match the selected attribute(s).
8.  Test “Select all” for attributes.
    -   Click **Select all** under attributes.
    -   Confirm that all attribute checkboxes become selected.
    -   Uncheck one attribute and verify that the select-all state updates correctly.
9.  Test sentiment filtering for review annotations.
    -   Enable **Enable sentiment filter**.
    -   Select positive, negative, or neutral.
    -   Apply filters and confirm that the review annotation display changes accordingly.
10. Test annotation display.
    -   In the results, verify that annotation output is grouped into:
        -   Title
        -   Description
        -   Review
    -   Confirm that highlighted review spans and annotation labels are displayed, and that the mouse cursor changes to a question mark when hovering over the annotated review text.
11. Test the legend.
    -   Confirm that the legend explains:
        -   positive
        -   negative
        -   neutral
        -   overlap
        -   query match
12. Test sorting.
    -   Change sorting to:
        -   Relevance: high to low
        -   Relevance: low to high
        -   Rating: high to low
        -   Rating: low to high
        -   Doc ID: high to low
        -   Doc ID: low to high
    -   Confirm that result ordering changes.
13. Test pagination size.
    -   Change **Results per page** to 10, 20, and 50.
    -   Confirm that the number of displayed results changes.
14. Test page navigation.
    -   Use **Previous** and **Next** buttons.
    -   Enter a page number manually in the page input box.
    -   Confirm that the displayed page changes correctly.
15. Test result details.
    -   Click **View Details** on a result.
    -   Confirm that document details load below the results section.
16. Test clearing filters.
    -   Click **Clear Filters**.
    -   Confirm that the query, filters, sort option, and page size reset to default values.
17. Test scrolling helpers.
    -   Scroll down the page.
    -   Confirm that the **Back to top** button appears.
    -   Click it and verify that it scrolls back to the top.
18. Report any bugs.
    -   Note any broken buttons, missing assets, incorrect filtering behavior, or display issues.
