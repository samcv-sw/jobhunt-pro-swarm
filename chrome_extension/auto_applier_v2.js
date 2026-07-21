/**
 * JobHunt Pro - Autonomous Chrome Auto-Applier V2
 * Supports Greenhouse, Lever, Workday, LinkedIn EasyApply
 */
(function() {
    console.log("[JobHunt Pro V2 Engine] Initialized on active job application portal.");

    const PORTAL_RULES = {
        greenhouse: ["#first_name", "#last_name", "#email", "#phone", "input[type='file']"],
        lever: ["input[name='name']", "input[name='email']", "input[name='phone']", "input[name='org']"],
        workday: ["input[data-automation-id='legalNameSection_firstName']", "input[data-automation-id='email']"],
        linkedin: [".jobs-easy-apply-modal"]
    };

    function detectPortal() {
        const url = window.location.href;
        if (url.includes("greenhouse.io")) return "greenhouse";
        if (url.includes("lever.co")) return "lever";
        if (url.includes("myworkdayjobs.com")) return "workday";
        if (url.includes("linkedin.com")) return "linkedin";
        return "generic";
    }

    async function autofillForm(candidateProfile) {
        const portal = detectPortal();
        console.log(`[JobHunt Pro V2] Auto-filling target portal: ${portal}`);
        
        // Match standard input fields dynamically
        const inputs = document.querySelectorAll("input, textarea");
        inputs.forEach(input => {
            const name = (input.name || input.id || input.placeholder || "").toLowerCase();
            if (name.includes("first") || name.includes("given")) {
                input.value = candidateProfile.firstName || "Sam";
            } else if (name.includes("last") || name.includes("family")) {
                input.value = candidateProfile.lastName || "Developer";
            } else if (name.includes("email")) {
                input.value = candidateProfile.email || "sam@jobhuntpro.io";
            } else if (name.includes("phone") || name.includes("mobile")) {
                input.value = candidateProfile.phone || "+1234567890";
            }
        });
        
        return { status: "success", portal: portal, filledCount: inputs.length };
    }

    window.JobHuntProAutoApplier = {
        detectPortal,
        autofillForm
    };
})();
