
function toggleComments(icon) {
    let postCard = icon.closest('.post-card');
    let commentBox = postCard.querySelector('.comment-section');

    if (commentBox.style.display === "block") {
        commentBox.style.display = "none";
    } else {
        commentBox.style.display = "block";
    }
}
function toggleLike(icon){
    let postId = icon.getAttribute('data-post');

    fetch(`/posts/like/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.json())
    .then(data => {
        let countSpan = icon.nextElementSibling;
        countSpan.innerText = data.count;
    });
}
function getCookie(name){
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

function toggleReplyForm(el) {
    const commentId = el.dataset.comment;
    const postUrl = el.dataset.url;

    let existing = el.nextElementSibling;
    if (existing && existing.classList.contains('reply-form')) {
        existing.remove();
        return;
    }

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = postUrl;
    form.className = 'reply-form';

    form.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
        <input type="hidden" name="parent_id" value="${commentId}">
        <input type="text" name="comment" placeholder="Write a reply..." required>
        <button type="submit">Reply</button>
    `;

    el.insertAdjacentElement('afterend', form);
}