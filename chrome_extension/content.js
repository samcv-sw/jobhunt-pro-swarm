// JobHunt Pro - Content Script for LinkedIn & Indeed
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_JOB_INFO") {
    let role = "";
    let company = "";

    // LinkedIn Job Page
    const linkedInTitle = document.querySelector(".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title, h1.top-card-layout__title");
    const linkedInCompany = document.querySelector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, a.topcard__org-name-link");

    // Indeed Job Page
    const indeedTitle = document.querySelector(".jobsearch-JobInfoHeader-title, h1.jobsearch-JobInfoHeader-title");
    const indeedCompany = document.querySelector("[data-testid='inlineHeader-companyName'], .jobsearch-CompanyInfoContainer");

    if (linkedInTitle) {
      role = linkedInTitle.innerText.trim();
      company = linkedInCompany ? linkedInCompany.innerText.trim() : "Target Employer";
    } else if (indeedTitle) {
      role = indeedTitle.innerText.trim();
      company = indeedCompany ? indeedCompany.innerText.trim() : "Target Employer";
    } else {
      const pageTitle = document.title.split("|")[0].split("-")[0].trim();
      role = pageTitle || "Professional Opportunity";
      company = "Gulf Enterprise";
    }

    sendResponse({ role: role, company: company });
  }
  return true;
});
