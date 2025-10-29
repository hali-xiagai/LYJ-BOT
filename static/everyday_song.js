let player;
let profile; // 全域變數

async function initLiff() {
    if (!profile) { // 確保只初始化一次
        await liff.init({ liffId: LIFF_ID });
        if (!liff.isLoggedIn()) {
            liff.login();
        }
        profile = await liff.getProfile();
        console.log("使用者名稱:", profile.displayName);
    }
}

//initLiff(); // 呼叫初始化

function onYouTubeIframeAPIReady() {
    if (!videoId) return;

    player = new YT.Player('player', {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: { 'autoplay': 0, 'controls': 1 },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    console.log("影片準備好，可以播放");
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.ENDED) {
        //alert("🎉 你已經看完今日推薦的音樂！");
        liff.closeWindow();
        if (!profile) {
            console.warn("profile 尚未取得，無法送出觀看紀錄");
            return;
        }

        fetch("/video_watched", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                userId: profile.userId,
                userName: profile.displayName,
                videoId: videoId
            })
        })
            .then(res => res.json())
            .then(data => console.log("response:", data))
            .catch(err => console.error("fetch error:", err));
    }
}


// 載入 YouTube API
const tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
document.body.appendChild(tag);
initLiff();
