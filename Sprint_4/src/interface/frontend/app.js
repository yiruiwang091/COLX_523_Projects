document.addEventListener("DOMContentLoaded", function () {
    const queryInput = document.getElementById("query");
    const annotatedOnlyCheckbox = document.getElementById("annotated_only");
    const annotationFilterGroup = document.getElementById("annotation-filter-group");
    const reviewSentimentOnlyCheckbox = document.getElementById("review_sentiment_only");
    const sentimentFilterGroup = document.getElementById("sentiment-filter-group");
    const selectAllAttributesCheckbox = document.getElementById("select_all_attributes");
    const form = document.getElementById("search-form");
    
    const backToTopBtn = document.getElementById("back-to-top-btn");

    const sortBySelect = document.getElementById("sort_by");
    const resultsDiv = document.getElementById("results");
    const resultsSummary = document.getElementById("results-summary");

    const pageSizeSelect = document.getElementById("page_size");
    const paginationControls = document.getElementById("pagination-controls");
    const prevPageBtn = document.getElementById("prev_page_btn");
    const nextPageBtn = document.getElementById("next_page_btn");
    const pageJumpInput = document.getElementById("page_jump_input");
    const pageTotalText = document.getElementById("page_total_text");
    const resultRange = document.getElementById("result-range");

    const detailsContainer = document.getElementById("details-container");
    const detailsDiv = document.getElementById("details");

    const PLACEHOLDER_IMAGE = "/frontend/placeholder.svg";

    let allResults = [];
    let currentPage = 1;

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        searchReviews();
    });

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function escapeRegExp(string) {
        return String(string).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function highlightQueryMatches(text, query) {
        const safeText = escapeHtml(text || "");
        const q = (query || "").trim();

        if (!q) return safeText;

        const terms = q.split(/\s+/).filter(Boolean);
        if (!terms.length) return safeText;

        const pattern = terms.map(escapeRegExp).join("|");
        const regex = new RegExp(`(${pattern})`, "gi");

        return safeText.replace(regex, `<span class="query-match">$1</span>`);
    }

    function sortResults(results, sortBy) {
        const items = [...results];

        if (sortBy === "relevance_asc") {
            items.sort((a, b) => (Number(a.score) || Infinity) - (Number(b.score) || Infinity));
        } else if (sortBy === "relevance_desc") {
            items.sort((a, b) => (Number(b.score) || -Infinity) - (Number(a.score) || -Infinity));
        } else if (sortBy === "rating_desc") {
            items.sort((a, b) => (Number(b.overall) || -Infinity) - (Number(a.overall) || -Infinity));
        } else if (sortBy === "rating_asc") {
            items.sort((a, b) => (Number(a.overall) || Infinity) - (Number(b.overall) || Infinity));
        } else if (sortBy === "doc_id_asc") {
            items.sort((a, b) =>
                String(a.doc_id).localeCompare(String(b.doc_id), undefined, { numeric: true })
            );
        } else if (sortBy === "doc_id_desc") {
            items.sort((a, b) =>
                String(b.doc_id).localeCompare(String(a.doc_id), undefined, { numeric: true })
            );
        } else {
            items.sort((a, b) => (Number(b.score) || -Infinity) - (Number(a.score) || -Infinity));
        }

        return items;
    }

    function getPageSize() {
        return Number(pageSizeSelect.value) || 20;
    }

    function getPaginatedResults(results, page, pageSize) {
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        return results.slice(start, end);
    }

    function updatePaginationUI(totalCount) {
        const pageSize = getPageSize();
        const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

        if (totalCount === 0) {
            paginationControls.classList.add("hidden");
            resultRange.textContent = "";
            pageJumpInput.value = 1;
            pageJumpInput.max = 1;
            pageTotalText.textContent = "of 1";
            return;
        }

        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        const start = (currentPage - 1) * pageSize + 1;
        const end = Math.min(currentPage * pageSize, totalCount);

        resultRange.textContent = `Showing ${start}–${end} of ${totalCount} results`;

        pageJumpInput.value = currentPage;
        pageJumpInput.max = totalPages;
        pageTotalText.textContent = `of ${totalPages}`;

        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;

        paginationControls.classList.remove("hidden");
    }

    function jumpToPage() {
        const totalPages = Math.max(1, Math.ceil(allResults.length / getPageSize()));
        let targetPage = Number(pageJumpInput.value);

        if (!Number.isFinite(targetPage)) {
            pageJumpInput.value = currentPage;
            return;
        }

        targetPage = Math.floor(targetPage);
        targetPage = Math.max(1, Math.min(totalPages, targetPage));

        if (targetPage !== currentPage) {
            currentPage = targetPage;
            renderResults();
            window.scrollTo({ top: 0, behavior: "smooth" });
        } else {
            pageJumpInput.value = currentPage;
        }
    }

    function normalizeReviewWhitespace(text) {
        if (!text) return "";
        return String(text)
            .replace(/\s*\n+\s*/g, " ")
            .replace(/[ \t]+/g, " ");
    }

    function getSelectedRadio(name) {
        const checked = document.querySelector(`input[name="${name}"]:checked`);
        return checked ? checked.value : "";
    }

    function getCheckedValues(name) {
        return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
            .map(el => el.value);
    }

    function clearCheckedValues(name) {
        document.querySelectorAll(`input[name="${name}"]`).forEach(el => {
            el.checked = false;
        });
    }

    function getAttributeCheckboxes() {
        return Array.from(document.querySelectorAll('input[name="attribute"]'));
    }

    function syncSelectAllAttributesState() {
        const attributeCheckboxes = getAttributeCheckboxes();
        const checkedCount = attributeCheckboxes.filter(cb => cb.checked).length;

        selectAllAttributesCheckbox.checked =
            attributeCheckboxes.length > 0 && checkedCount === attributeCheckboxes.length;

        selectAllAttributesCheckbox.indeterminate =
            checkedCount > 0 && checkedCount < attributeCheckboxes.length;
    }
    
    function updateBackToTopVisibility() {
        if (window.scrollY > 100) {
            backToTopBtn.classList.remove("hidden");
        } else {
            backToTopBtn.classList.add("hidden");
        }
    }

    function updateFilterVisibility() {
        const showAnnotationFilters = annotatedOnlyCheckbox.checked;
        annotationFilterGroup.classList.toggle("hidden", !showAnnotationFilters);

        if (!showAnnotationFilters) {
            clearCheckedValues("attribute");
            selectAllAttributesCheckbox.checked = false;
            selectAllAttributesCheckbox.indeterminate = false;

            reviewSentimentOnlyCheckbox.checked = false;
            clearCheckedValues("sentiment");
            sentimentFilterGroup.classList.add("hidden");
            return;
        }

        const showSentimentFilters = reviewSentimentOnlyCheckbox.checked;
        sentimentFilterGroup.classList.toggle("hidden", !showSentimentFilters);

        if (!showSentimentFilters) {
            clearCheckedValues("sentiment");
        }

        syncSelectAllAttributesState();
    }

    annotatedOnlyCheckbox.addEventListener("change", updateFilterVisibility);
    reviewSentimentOnlyCheckbox.addEventListener("change", updateFilterVisibility);

    selectAllAttributesCheckbox.addEventListener("change", function () {
        const checked = this.checked;
        getAttributeCheckboxes().forEach(cb => {
            cb.checked = checked;
        });
        this.indeterminate = false;
    });

    getAttributeCheckboxes().forEach(cb => {
        cb.addEventListener("change", syncSelectAllAttributesState);
    });

    sortBySelect.addEventListener("change", function () {
        currentPage = 1;
        renderResults();
    });

    pageSizeSelect.addEventListener("change", function () {
        currentPage = 1;
        renderResults();
    });

    prevPageBtn.addEventListener("click", function () {
        if (currentPage > 1) {
            currentPage -= 1;
            renderResults();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    });

    nextPageBtn.addEventListener("click", function () {
        const totalPages = Math.max(1, Math.ceil(allResults.length / getPageSize()));
        if (currentPage < totalPages) {
            currentPage += 1;
            renderResults();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    });
    
    backToTopBtn.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
    
    window.addEventListener("scroll", updateBackToTopVisibility);

    pageJumpInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            jumpToPage();
        }
    });

    pageJumpInput.addEventListener("blur", function () {
        jumpToPage();
    });

    function buildSnippetText(r) {
        const text = r.snippet || "";
        const maxLen = 120;
        return text.length > maxLen ? text.substring(0, maxLen) + "..." : text;
    }

    function groupAnnotations(annotations) {
        const grouped = {
            title: [],
            description: [],
            review: []
        };

        (annotations || []).forEach(a => {
            const section = (a.section || "").toLowerCase();

            if (section === "title") {
                grouped.title.push(a);
            } else if (section === "description") {
                grouped.description.push(a);
            } else if (section === "review") {
                grouped.review.push(a);
            }
        });

        return grouped;
    }

    function filterAnnotationsForDisplay(
        annotations,
        selectedAttributes,
        selectedSentiments,
        applyReviewSentimentOnly
    ) {
        return (annotations || []).filter(a => {
            const section = (a.section || "").toLowerCase();

            const matchAttribute =
                selectedAttributes.length === 0 || selectedAttributes.includes(a.label || "");

            let matchSentiment = true;
            if (applyReviewSentimentOnly && section === "review") {
                matchSentiment =
                    selectedSentiments.length === 0 || selectedSentiments.includes(a.sentiment || "");
            }

            return matchAttribute && matchSentiment;
        });
    }

    function renderSpanLabelChips(items) {
        if (!items || items.length === 0) {
            return `<div class="muted">No matching annotations.</div>`;
        }

        return `
            <div class="annotation-chip-list">
                ${items.map(a => `
                    <div class="annotation-chip">
                        <span class="span-text">${escapeHtml(a.text || "")}</span>
                        <span class="meta">(${escapeHtml(a.label || "")}${a.sentiment ? ", " + escapeHtml(a.sentiment) : ""})</span>
                    </div>
                `).join("")}
            </div>
        `;
    }

    function highlightReviewText(reviewText, reviewAnnotations, query) {
        if (!reviewText) {
            return `<div class="muted">No review text available.</div>`;
        }

        if (!reviewAnnotations || reviewAnnotations.length === 0) {
            return `<div class="review-highlight-box">${highlightQueryMatches(reviewText, query)}</div>`;
        }

        const validAnnotations = [...reviewAnnotations]
            .filter(a =>
                typeof a.start === "number" &&
                typeof a.end === "number" &&
                a.end > a.start
            )
            .map(a => ({
                ...a,
                start: Math.max(0, a.start),
                end: Math.min(reviewText.length, a.end)
            }))
            .filter(a => a.end > a.start);

        if (validAnnotations.length === 0) {
            return `<div class="review-highlight-box">${highlightQueryMatches(reviewText, query)}</div>`;
        }

        const boundaries = new Set([0, reviewText.length]);
        validAnnotations.forEach(a => {
            boundaries.add(a.start);
            boundaries.add(a.end);
        });

        const points = Array.from(boundaries).sort((a, b) => a - b);

        let html = "";

        for (let i = 0; i < points.length - 1; i++) {
            const segStart = points[i];
            const segEnd = points[i + 1];

            if (segEnd <= segStart) continue;

            const rawSegmentText = reviewText.slice(segStart, segEnd);
            const segmentText = normalizeReviewWhitespace(rawSegmentText);

            if (!segmentText) continue;

            const covering = validAnnotations.filter(a => a.start <= segStart && a.end >= segEnd);

            if (covering.length === 0) {
                html += highlightQueryMatches(segmentText, query);
                continue;
            }

            const tooltipText = covering
                .map(a => `${a.label || "annotation"}${a.sentiment ? " | " + a.sentiment : ""}`)
                .join(" ; ");

            const sentiments = covering
                .map(a => (a.sentiment || "").toLowerCase())
                .filter(Boolean);

            let sentimentClass = "sentiment-neutral";
            if (sentiments.includes("negative")) {
                sentimentClass = "sentiment-negative";
            } else if (sentiments.includes("positive")) {
                sentimentClass = "sentiment-positive";
            }

            const overlapClass = covering.length >= 2 ? "overlap" : "";

            html += `
                <span
                    class="review-segment annotated ${sentimentClass} ${overlapClass}"
                    title="${escapeHtml(tooltipText)}"
                >
                    ${highlightQueryMatches(segmentText, query)}
                </span>
            `;
        }

        const legend = validAnnotations.map(a => {
            const label = escapeHtml(a.label || "");
            const sentiment = escapeHtml(a.sentiment || "");
            const text = escapeHtml(a.text || reviewText.slice(a.start, a.end) || "");
            return `
                <div class="review-legend-item">
                    ${text} → ${label}${sentiment ? " | " + sentiment : ""}
                </div>
            `;
        }).join("");

        return `
            <div class="review-highlight-box">${html}</div>
            <div class="review-legend">${legend}</div>
        `;
    }

    function renderAnnotationBlock(r, currentFilters) {
        const annotations = r.annotations || [];

        if (!annotations.length) {
            return `<div class="annotations"><h4>Annotation Result</h4><div class="muted">No annotations.</div></div>`;
        }

        const filteredAnnotations = filterAnnotationsForDisplay(
            annotations,
            currentFilters.attributes,
            currentFilters.sentiments,
            currentFilters.reviewSentimentOnly
        );

        if (!filteredAnnotations.length) {
            return `<div class="annotations"><h4>Annotation Result</h4><div class="muted">No matching annotations for current filters.</div></div>`;
        }

        const grouped = groupAnnotations(filteredAnnotations);
        const reviewText = r.reviewText || r.review_text || "";

        return `
            <div class="annotations">
                <h4>Annotation Result</h4>

                <div class="annotation-section">
                    <div class="annotation-section-title">Title</div>
                    ${renderSpanLabelChips(grouped.title)}
                </div>

                <div class="annotation-section">
                    <div class="annotation-section-title">Description</div>
                    ${renderSpanLabelChips(grouped.description)}
                </div>

                <div class="annotation-section">
                    <div class="annotation-section-title">Review</div>
                    ${highlightReviewText(reviewText, grouped.review, currentFilters.query)}
                </div>
            </div>
        `;
    }

    function getCurrentFilters() {
        return {
            query: queryInput.value.trim(),
            field: getSelectedRadio("field"),
            annotatedOnly: annotatedOnlyCheckbox.checked,
            attributes: getCheckedValues("attribute"),
            reviewSentimentOnly: reviewSentimentOnlyCheckbox.checked,
            sentiments: getCheckedValues("sentiment"),
            sortBy: sortBySelect.value || "relevance_desc"
        };
    }

    function renderResultsSummary(totalCount, query) {
        if (totalCount === 0) {
            resultsSummary.classList.add("hidden");
            resultsSummary.textContent = "";
            return;
        }

        const queryText = query ? ` for "${query}"` : "";
        resultsSummary.textContent = `${totalCount} results found${queryText}`;
        resultsSummary.classList.remove("hidden");
    }

    function renderResults() {
        const filters = getCurrentFilters();
        const sortedResults = sortResults(allResults, filters.sortBy);
        const pageSize = getPageSize();
        const pageResults = getPaginatedResults(sortedResults, currentPage, pageSize);

        resultsDiv.innerHTML = "";
        renderResultsSummary(sortedResults.length, filters.query);

        if (!sortedResults.length) {
            resultsDiv.innerHTML = `<div class="message muted">No results found.</div>`;
            paginationControls.classList.add("hidden");
            return;
        }

        pageResults.forEach(r => {
            const resultBox = document.createElement("div");
            resultBox.className = "result";

            const annotationHtml = renderAnnotationBlock(r, filters);

            const imageValue = Array.isArray(r.imageURL) ? r.imageURL[0] : r.imageURL;

            const imageHtml = imageValue
                ? `<img src="${escapeHtml(imageValue)}" alt="Product image"
                        onerror="this.onerror=null; this.parentElement.innerHTML='<div class=&quot;image-placeholder&quot;><img src=&quot;${PLACEHOLDER_IMAGE}&quot; alt=&quot;No image available&quot;></div>';">`
                : `<div class="image-placeholder">
                        <img src="${PLACEHOLDER_IMAGE}" alt="No image available">
                   </div>`;

            const ratingText =
                (r.overall !== null && r.overall !== undefined && r.overall !== "")
                    ? `${escapeHtml(r.overall)} / 5`
                    : "N/A";

            const titleHtml = highlightQueryMatches(r.title || "(no title)", filters.query);
            const snippetHtml = highlightQueryMatches(buildSnippetText(r), filters.query);

            resultBox.innerHTML = `
                <div class="result-top">
                    <div class="result-image">
                        ${imageHtml}
                    </div>

                    <div class="result-main">
                        <div class="result-line"><strong>Doc ID:</strong> ${escapeHtml(r.doc_id)}</div>
                        <div class="result-line"><strong>Title:</strong> ${titleHtml}</div>
                        <div class="result-line snippet"><strong>Snippet:</strong> ${snippetHtml}</div>
                        <div class="result-line rating"><strong>Rating:</strong> ${ratingText}</div>
                        <div class="result-line score">
                            <strong class="tooltip">
                                Retrieval relevance
                                <span class="tooltip-text">
                                    A relevance score from the search engine. Higher values indicate that the review is more relevant to the query.
                                </span>
                            </strong>:
                            ${typeof r.score === "number" ? r.score.toFixed(4) : ""}
                        </div>
                        ${annotationHtml}
                        <div class="result-actions">
                            <button type="button" onclick="viewDetails('${String(r.doc_id)}')">View Details</button>
                        </div>
                    </div>
                </div>
            `;

            resultsDiv.appendChild(resultBox);
        });

        updatePaginationUI(sortedResults.length);
    }

    window.clearFilters = function () {
        queryInput.value = "";
        document.querySelector('input[name="field"][value="all"]').checked = true;

        annotatedOnlyCheckbox.checked = false;
        reviewSentimentOnlyCheckbox.checked = false;

        clearCheckedValues("attribute");
        clearCheckedValues("sentiment");

        selectAllAttributesCheckbox.checked = false;
        selectAllAttributesCheckbox.indeterminate = false;

        sortBySelect.value = "relevance_desc";
        pageSizeSelect.value = "20";

        allResults = [];
        currentPage = 1;

        updateFilterVisibility();

        resultsDiv.innerHTML = `<div class="message muted">Filters cleared.</div>`;
        resultsSummary.classList.add("hidden");
        resultsSummary.textContent = "";
        paginationControls.classList.add("hidden");

        detailsContainer.style.display = "none";
        detailsDiv.textContent = "";
    };

    window.searchReviews = async function () {
        try {
            const filters = getCurrentFilters();
            const params = new URLSearchParams();

            params.append("q", filters.query);
            params.append("field", filters.field);
            params.append("annotated_only", String(filters.annotatedOnly));

            filters.attributes.forEach(v => params.append("attribute", v));

            if (filters.reviewSentimentOnly) {
                filters.sentiments.forEach(v => params.append("sentiment", v));
            }

            const url = `/api/search?${params.toString()}`;

            resultsDiv.innerHTML = `<div class="message muted">Loading...</div>`;
            resultsSummary.classList.add("hidden");
            paginationControls.classList.add("hidden");
            detailsContainer.style.display = "none";
            detailsDiv.textContent = "";

            const res = await fetch(url);

            if (!res.ok) {
                throw new Error(`HTTP error: ${res.status}`);
            }

            const data = await res.json();

            allResults = data.results || [];
            currentPage = 1;

            renderResults();
        } catch (err) {
            console.error(err);
            allResults = [];
            currentPage = 1;
            resultsSummary.classList.add("hidden");
            resultsDiv.innerHTML = `<div class="message error">Error: ${escapeHtml(err.message)}</div>`;
            paginationControls.classList.add("hidden");
        }
    };

    window.viewDetails = async function (docId) {
        try {
            detailsContainer.style.display = "block";
            detailsDiv.textContent = "Loading document details...";

            const res = await fetch(`/api/doc/${encodeURIComponent(docId)}`);

            if (!res.ok) {
                throw new Error(`HTTP error: ${res.status}`);
            }

            const data = await res.json();

            detailsDiv.textContent = JSON.stringify(data, null, 2);
            detailsContainer.scrollIntoView({ behavior: "smooth" });
        } catch (err) {
            console.error(err);
            detailsContainer.style.display = "block";
            detailsDiv.textContent = `Failed to load document details: ${err.message}`;
        }
    };

    updateFilterVisibility();
    updateBackToTopVisibility();
});