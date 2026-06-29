function toggleComments(icon) {
    let postCard = icon.closest('.post-card');
    let commentBox = postCard.querySelector('.comment-section');
    commentBox.style.display = commentBox.style.display === "block" ? "none" : "block";
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}

function toggleLike(icon) {
    let postId = icon.dataset.post;
    fetch(`/posts/like/${postId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        icon.classList.toggle("active", data.liked);
        icon.nextElementSibling.innerText = data.count;
    });
}

/* ---------- Comment / reply submission (delegated — works for dynamic forms too) ---------- */

document.addEventListener("submit", function (e) {
    const form = e.target;

    if (!form.classList.contains("comment-form") && !form.classList.contains("reply-form")) {
        return;
    }

    e.preventDefault();

    fetch(form.action, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        },
        body: new FormData(form)
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) return;

        if (form.classList.contains("reply-form")) {
            handleReplyInsert(form, data);
        } else {
            const list = form.closest(".comment-section").querySelector(".comments-list");
            list.insertAdjacentHTML("beforeend", data.html);
            form.reset();
        }
    });
});

function handleReplyInsert(form, data) {
    const parentTopId = data.parent_top_id;
    form.remove();

    if (!parentTopId) {
        const list = form.closest(".comment-section").querySelector(".comments-list");
        list.insertAdjacentHTML("beforeend", data.html);
        return;
    }

    const topComment = document.getElementById(`comment-${parentTopId}`);
    if (!topComment) return;

    let wrapper = topComment.parentElement.querySelector(`.replies-wrapper[data-top="${parentTopId}"]`);

    if (!wrapper) {
        // first reply on this thread - the wrapper didn't exist yet, build it
        wrapper = document.createElement("div");
        wrapper.className = "replies-wrapper";
        wrapper.dataset.top = parentTopId;
        wrapper.innerHTML = `
            <button type="button" class="show-replies" onclick="toggleReplies(this)">
                <span class="show-replies-icon">⌃</span>
                View 1 reply
            </button>
            <div class="replies-container" id="replies-${parentTopId}" style="display:block;"></div>
        `;
        topComment.insertAdjacentElement("afterend", wrapper);
    }

    const container = wrapper.querySelector(".replies-container");
    container.insertAdjacentHTML("beforeend", data.html);
    container.style.display = "block";

    const btn = wrapper.querySelector(".show-replies");
    const count = container.querySelectorAll(".comment").length;
    btn.innerHTML = `<span class="show-replies-icon">⌃</span> View ${count} repl${count === 1 ? "y" : "ies"}`;
}

function toggleReplyForm(el) {
    const commentId = el.dataset.comment;
    const postUrl = el.dataset.url;

    const actions = el.closest(".comment-actions");
    let existing = actions.nextElementSibling;

    if (existing?.classList.contains("reply-form")) {
        existing.remove();
        return;
    }

    const form = document.createElement("form");
    form.className = "reply-form";
    form.method = "POST";
    form.action = postUrl;

    form.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
        <input type="hidden" name="parent_id" value="${commentId}">
        <input type="text" name="comment" placeholder="Write a reply..." required>
        <button type="submit">Reply</button>
    `;

    actions.insertAdjacentElement("afterend", form);
}

function toggleReplies(btn) {
    const wrapper = btn.closest(".replies-wrapper");
    const container = wrapper.querySelector(".replies-container");
    const isHidden = container.style.display !== "block";
    container.style.display = isHidden ? "block" : "none";
    btn.querySelector(".show-replies-icon").textContent = isHidden ? "⌃" : "⌄";
}

/* ---------- Edit / Delete (delegated — fixes dynamic comments + missing attachCommentActionEvents) ---------- */

document.addEventListener("click", function (e) {

    const deleteBtn = e.target.closest(".comment-delete-btn");
    if (deleteBtn) {
        if (!confirm("Delete this comment?")) return;

        fetch(deleteBtn.dataset.url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const comment = document.getElementById(`comment-${data.comment_id}`);
                if (comment) comment.remove();
            }
        });
        return;
    }

    const editBtn = e.target.closest(".comment-edit-btn");
    if (editBtn) {
        startCommentEdit(editBtn);
        return;
    }

    const cancelBtn = e.target.closest(".cancel-comment-btn");
    if (cancelBtn) {
        const comment = cancelBtn.closest(".comment");
        restoreCommentActions(comment, comment.dataset.originalText, comment.dataset.actionsHtml);
        return;
    }

    const saveBtn = e.target.closest(".save-comment-btn");
    if (saveBtn) {
        saveCommentEdit(saveBtn);
        return;
    }
});

function startCommentEdit(editBtn) {
    const comment = editBtn.closest(".comment");
    const textDiv = comment.querySelector("[data-comment-text]");
    const actions = editBtn.closest(".comment-actions");

    const originalText = textDiv.innerText.trim();

    comment.dataset.originalText = originalText;
    comment.dataset.actionsHtml = actions.innerHTML;
    comment.dataset.editUrl = editBtn.dataset.url;

    textDiv.innerHTML = `<textarea class="comment-edit-input">${originalText}</textarea>`;

    actions.innerHTML = `
        <button type="button" class="save-comment-btn">Save</button>
        <button type="button" class="cancel-comment-btn">Cancel</button>
    `;
}

function restoreCommentActions(comment, originalText, actionsHtml) {
    const textDiv = comment.querySelector("[data-comment-text]");
    textDiv.innerText = originalText;
    comment.querySelector(".comment-actions").innerHTML = actionsHtml;
}

function saveCommentEdit(saveBtn) {
    const comment = saveBtn.closest(".comment");
    const textarea = comment.querySelector(".comment-edit-input");
    const editUrl = comment.dataset.editUrl;

    fetch(editUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        },
        body: new URLSearchParams({ text: textarea.value })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert(data.error || "Could not save comment.");
            return;
        }
        restoreCommentActions(comment, data.text, comment.dataset.actionsHtml);
    });
}
function toggleRepost(icon) {
    const postId = icon.dataset.post;
    fetch(`/posts/repost/${postId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    })
    .then(res => res.json())
    .then(data => {
        icon.classList.toggle("active", data.reposted);
        icon.nextElementSibling.innerText = data.count;
    });
}


function toggleShareMenu(btn) {
    // close other open menus first
    document.querySelectorAll(".share-menu").forEach(menu => {
        if (menu !== btn.nextElementSibling) {
            menu.style.display = "none";
        }
    });

    const menu = btn.nextElementSibling;
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

function closeShareMenu(btn) {
    btn.closest(".share-menu").style.display = "none";
}

function copyPostLink(btn) {
    const postId = btn.dataset.post;

    const url = `${window.location.origin}/posts/${postId}/`;

    navigator.clipboard.writeText(url).then(() => {
        btn.innerText = "Copied!";
        setTimeout(() => {
            btn.innerText = "Copy link";
        }, 1200);
    });

    btn.closest(".share-menu").style.display = "none";
}

// optional: click outside closes menu
document.addEventListener("click", function (e) {
    if (!e.target.closest(".share-wrapper")) {
        document.querySelectorAll(".share-menu").forEach(m => m.style.display = "none");
    }
});
function toggleBookmark(el) {
    let postId = el.getAttribute("data-post");
    fetch(`/posts/bookmark/${postId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    })
    .then(res => res.json())
    .then(data => {
        el.classList.toggle("active", data.status === "bookmarked");
    });
}

function togglePostMenu(btn) {
    let menu = btn.nextElementSibling;

    // close other open menus
    document.querySelectorAll('.options-menu').forEach(m => {
        if (m !== menu) m.style.display = 'none';
    });

    menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.options-wrapper')) {
        document.querySelectorAll('.options-menu').forEach(m => {
            m.style.display = 'none';
        });
    }
});