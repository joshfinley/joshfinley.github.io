// Function to create or update footnotes
function updateFootnotes() {
  // Set your own threshold width in pixels
  const thresholdWidth = 1024;

  // Get the current window width
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth;

  // Remove existing cloned footnotes
  const existingClones = document.querySelectorAll('.cloned-footnote');
  existingClones.forEach(clone => clone.remove());

  // Don't create footnotes for narrow displays
  if (viewportWidth < thresholdWidth) {
    return;
  }

  // Update this line to also search for fancyquote footnotes
  const footnoteReferences = document.querySelectorAll('[id^="ref-"], .fancyquote-footnote');

  // Get the .content-area element to align the cloned footnotes
  const contentArea = document.querySelector('.content-area');

  if (!contentArea) return;

  // Calculate the right edge position of the .content-area
  const contentAreaRect = contentArea.getBoundingClientRect();
  const contentAreaRight = contentAreaRect.right + window.pageXOffset;

  // Convert NodeList to Array and filter out duplicates based on id
  const uniqueFootnoteReferences = Array.from(new Set(Array.from(footnoteReferences).map(ref => ref.id)))
    .map(id => document.querySelector(`#${id}`));

  // Sort footnotes by their vertical position
  uniqueFootnoteReferences.sort((a, b) => {
    return a.getBoundingClientRect().top - b.getBoundingClientRect().top;
  });

  // Initialize a variable to keep track of the bottom of the last footnote
  let lastFootnoteBottom = 0;

  uniqueFootnoteReferences.forEach((ref) => {
    // Get the id of the reference to find its corresponding footnote
    const refId = ref.id.replace("ref-", "").replace("fancyquote-", "");
    const footnote = document.querySelector(`#fn-${refId}`);

    // Make sure the footnote exists
    if (!footnote) return;

    // Create a clone of the footnote
    const clonedFootnote = footnote.cloneNode(true);

    // Add additional class for styling
    clonedFootnote.classList.add('cloned-footnote');

    // Find the position of the original footnote reference
    const rect = ref.getBoundingClientRect();
    let topPos = Math.max(rect.top + window.pageYOffset, lastFootnoteBottom);

    // Position the cloned footnote next to the reference
    clonedFootnote.style.position = 'absolute';
    clonedFootnote.style.left = `${contentAreaRight}px`;
    clonedFootnote.style.top = `${topPos}px`;

    // Append the cloned footnote to the body temporarily to measure it
    document.body.appendChild(clonedFootnote);

    // Update the bottom of the last footnote
    lastFootnoteBottom = topPos + clonedFootnote.offsetHeight;
  });
}

// Update footnotes on page load
document.addEventListener('DOMContentLoaded', updateFootnotes);

// Update footnotes on window resize
window.addEventListener('resize', updateFootnotes);
