document.addEventListener("DOMContentLoaded", function () {

const queryInput = document.getElementById("query");
const annotatedOnlyCheckbox = document.getElementById("annotated_only");
const annotationFilterGroup = document.getElementById("annotation-filter-group");
const reviewSentimentOnlyCheckbox = document.getElementById("review_sentiment_only");
const sentimentFilterGroup = document.getElementById("sentiment-filter-group");
const selectAllAttributesCheckbox = document.getElementById("select_all_attributes");
const form = document.getElementById("search-form");


/* form submit */

form.addEventListener("submit", function(event){
    event.preventDefault();
    searchReviews();
});


/* helpers */

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;")
        .replace(/"/g,"&quot;")
        .replace(/'/g,"&#039;");
}

function escapeRegExp(string){
    return string.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
}


/* query highlight */

function highlightQueryMatches(text,query){

    const safeText = escapeHtml(text || "");
    const q = (query || "").trim();

    if(!q) return safeText;

    const terms = q.split(/\s+/).filter(Boolean);
    if(!terms.length) return safeText;

    const pattern = terms.map(escapeRegExp).join("|");
    const regex = new RegExp(`(${pattern})`,"gi");

    return safeText.replace(regex,`<span class="query-match">$1</span>`);
}


/* sorting */

function sortResults(results,sortBy){

    const items=[...results];

    if(sortBy==="rating_desc"){
        items.sort((a,b)=>(Number(b.overall)||-Infinity)-(Number(a.overall)||-Infinity));
    }

    else if(sortBy==="rating_asc"){
        items.sort((a,b)=>(Number(a.overall)||Infinity)-(Number(b.overall)||Infinity));
    }

    else if(sortBy==="doc_id_asc"){
        items.sort((a,b)=>String(a.doc_id).localeCompare(String(b.doc_id),undefined,{numeric:true}));
    }

    else if(sortBy==="doc_id_desc"){
        items.sort((a,b)=>String(b.doc_id).localeCompare(String(a.doc_id),undefined,{numeric:true}));
    }

    else{
        items.sort((a,b)=>(Number(b.score)||-Infinity)-(Number(a.score)||-Infinity));
    }

    return items;
}


/* filter helpers */

function getSelectedRadio(name){
    const checked=document.querySelector(`input[name="${name}"]:checked`);
    return checked?checked.value:"";
}

function getCheckedValues(name){
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
    .map(el=>el.value);
}

function clearCheckedValues(name){
    document.querySelectorAll(`input[name="${name}"]`).forEach(el=>{
        el.checked=false;
    });
}


/* attributes */

function getAttributeCheckboxes(){
    return Array.from(document.querySelectorAll('input[name="attribute"]'));
}

function syncSelectAllAttributesState(){

    const attributeCheckboxes=getAttributeCheckboxes();
    const checkedCount=attributeCheckboxes.filter(cb=>cb.checked).length;

    selectAllAttributesCheckbox.checked=
        attributeCheckboxes.length>0 && checkedCount===attributeCheckboxes.length;

    selectAllAttributesCheckbox.indeterminate=
        checkedCount>0 && checkedCount<attributeCheckboxes.length;
}


/* filter visibility */

function updateFilterVisibility(){

    const showAnnotationFilters=annotatedOnlyCheckbox.checked;

    annotationFilterGroup.classList.toggle("hidden",!showAnnotationFilters);

    if(!showAnnotationFilters){

        clearCheckedValues("attribute");
        selectAllAttributesCheckbox.checked=false;
        selectAllAttributesCheckbox.indeterminate=false;

        reviewSentimentOnlyCheckbox.checked=false;
        clearCheckedValues("sentiment");

        sentimentFilterGroup.classList.add("hidden");

        return;
    }

    const showSentimentFilters=reviewSentimentOnlyCheckbox.checked;

    sentimentFilterGroup.classList.toggle("hidden",!showSentimentFilters);

    if(!showSentimentFilters){
        clearCheckedValues("sentiment");
    }

    syncSelectAllAttributesState();
}


annotatedOnlyCheckbox.addEventListener("change",updateFilterVisibility);
reviewSentimentOnlyCheckbox.addEventListener("change",updateFilterVisibility);


document.getElementById("sort_by").addEventListener("change",searchReviews);


selectAllAttributesCheckbox.addEventListener("change",function(){

    const checked=this.checked;

    getAttributeCheckboxes().forEach(cb=>{
        cb.checked=checked;
    });

    this.indeterminate=false;
});


getAttributeCheckboxes().forEach(cb=>{
    cb.addEventListener("change",syncSelectAllAttributesState);
});


/* build snippet */

function buildSnippetText(r){

    const text=r.snippet||"";
    const maxLen=120;

    if(text.length>maxLen){
        return text.substring(0,maxLen)+"...";
    }

    return text;
}


/* annotation grouping */

function groupAnnotations(annotations){

    const grouped={
        title:[],
        description:[],
        review:[]
    };

    (annotations||[]).forEach(a=>{

        const section=(a.section||"").toLowerCase();

        if(section==="title") grouped.title.push(a);
        else if(section==="description") grouped.description.push(a);
        else if(section==="review") grouped.review.push(a);

    });

    return grouped;
}


/* annotation display */

function renderSpanLabelChips(items){

    if(!items || items.length===0){
        return `<div class="muted">No matching annotations.</div>`;
    }

    return `
    <div class="annotation-chip-list">

        ${items.map(a=>`

        <div class="annotation-chip">
        <span class="span-text">${escapeHtml(a.text||"")}</span>
        <span class="meta">(${escapeHtml(a.label||"")}${a.sentiment?", "+escapeHtml(a.sentiment):""})</span>
        </div>

        `).join("")}

    </div>
    `;
}


/* highlight review text */

function highlightReviewText(reviewText,reviewAnnotations,query){

    if(!reviewText){
        return `<div class="muted">No review text available.</div>`;
    }

    if(!reviewAnnotations || reviewAnnotations.length===0){
        return `<div class="review-highlight-box">${highlightQueryMatches(reviewText,query)}</div>`;
    }

    let html="";

    let last=0;

    reviewAnnotations.forEach(a=>{

        const start=a.start;
        const end=a.end;

        html+=highlightQueryMatches(reviewText.slice(last,start),query);

        let sentimentClass="sentiment-neutral";

        if(a.sentiment==="positive") sentimentClass="sentiment-positive";
        if(a.sentiment==="negative") sentimentClass="sentiment-negative";

        html+=`<span class="review-segment annotated ${sentimentClass}">
        ${highlightQueryMatches(reviewText.slice(start,end),query)}
        </span>`;

        last=end;

    });

    html+=highlightQueryMatches(reviewText.slice(last),query);

    return `<div class="review-highlight-box">${html}</div>`;
}


/* render annotation block */

function renderAnnotationBlock(r,currentFilters){

    const annotations=r.annotations||[];

    if(!annotations.length){
        return `<div class="annotations"><div class="muted">No annotations.</div></div>`;
    }

    const grouped=groupAnnotations(annotations);

    const reviewText=r.reviewText||r.review_text||"";

    return `
    <div class="annotations">

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
    ${highlightReviewText(reviewText,grouped.review,currentFilters.query)}
    </div>

    </div>
    `;
}


/* filters */

function getCurrentFilters(){

    return{
        query:document.getElementById("query").value.trim(),
        field:getSelectedRadio("field"),
        annotatedOnly:document.getElementById("annotated_only").checked,
        attributes:getCheckedValues("attribute"),
        reviewSentimentOnly:document.getElementById("review_sentiment_only").checked,
        sentiments:getCheckedValues("sentiment"),
        sortBy:document.getElementById("sort_by").value
    };

}


/* clear filters */

window.clearFilters=function(){

    document.getElementById("query").value="";

    document.querySelector(`input[name="field"][value="all"]`).checked=true;

    annotatedOnlyCheckbox.checked=false;

    reviewSentimentOnlyCheckbox.checked=false;

    clearCheckedValues("attribute");
    clearCheckedValues("sentiment");

    selectAllAttributesCheckbox.checked=false;

    updateFilterVisibility();

};


/* search */

window.searchReviews=async function(){

const resultsDiv=document.getElementById("results");

try{

const filters=getCurrentFilters();

const params=new URLSearchParams();

params.append("q",filters.query);
params.append("field",filters.field);
params.append("annotated_only",filters.annotatedOnly);

filters.attributes.forEach(v=>params.append("attribute",v));

if(filters.reviewSentimentOnly){

params.append("review_sentiment_only","true");

filters.sentiments.forEach(v=>params.append("sentiment",v));

}

const url=`/api/search?${params.toString()}`;

resultsDiv.innerHTML=`<div class="message muted">Loading...</div>`;

const res=await fetch(url);

const data=await res.json();

const sortedResults=sortResults(data.results||[],filters.sortBy);

resultsDiv.innerHTML="";

if(!sortedResults.length){

resultsDiv.innerHTML=`<div class="message muted">No results found.</div>`;

return;

}

sortedResults.forEach(r=>{

const resultBox=document.createElement("div");

resultBox.className="result";

const annotationHtml=renderAnnotationBlock(r,filters);

const titleHtml=highlightQueryMatches(r.title||"(no title)",filters.query);

const snippetHtml=highlightQueryMatches(buildSnippetText(r),filters.query);

const ratingText=r.overall?`${escapeHtml(r.overall)} / 5`:"N/A";

resultBox.innerHTML=`

<div class="result-top">

<div class="result-main">

<div class="result-line"><strong>Doc ID:</strong> ${escapeHtml(r.doc_id)}</div>

<div class="result-line"><strong>Title:</strong> ${titleHtml}</div>

<div class="result-line snippet"><strong>Snippet:</strong> ${snippetHtml}</div>

<div class="result-line rating"><strong>Rating:</strong> ${ratingText}</div>

<div class="result-line score"><strong>Score:</strong> ${typeof r.score==="number"?r.score.toFixed(4):""}</div>

${annotationHtml}

<div class="result-actions">
<button onclick="viewDetails('${String(r.doc_id)}')">View Details</button>
</div>

</div>

</div>
`;

resultsDiv.appendChild(resultBox);

});

}

catch(err){

resultsDiv.innerHTML=`<div class="message error">Error: ${escapeHtml(err.message)}</div>`;

}

};


/* view details */

window.viewDetails=async function(docId){

const detailsContainer=document.getElementById("details-container");

const detailsDiv=document.getElementById("details");

try{

detailsContainer.style.display="block";

detailsDiv.textContent="Loading document details...";

const res=await fetch(`/api/doc/${encodeURIComponent(docId)}`);

const data=await res.json();

detailsDiv.textContent=JSON.stringify(data,null,2);

detailsContainer.scrollIntoView({behavior:"smooth"});

}

catch(err){

detailsDiv.textContent=`Failed to load document details: ${err.message}`;

}

};


updateFilterVisibility();

});