/*************************************************************************
* ADOBE CONFIDENTIAL
* ___________________
*
*  Copyright 2015 Adobe Systems Incorporated
*  All Rights Reserved.
*
* NOTICE:  All information contained herein is, and remains
* the property of Adobe Systems Incorporated and its suppliers,
* if any.  The intellectual and technical concepts contained
* herein are proprietary to Adobe Systems Incorporated and its
* suppliers and are protected by all applicable intellectual property laws,
* including trade secret and or copyright laws.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Adobe Systems Incorporated.
**************************************************************************/
const FTE_STATE_STORAGE_KEY="embeddedPDFTouchPointFTEState";class EmbeddedPDFTouchPointCoachMark{shouldResetFteToolTip(t,e){return-1!==t?.resetDay&&e>t?.resetDay}async initFteStateAndConfig(t){const e=(new Date).getTime();let i={count:0,nextDate:e};i=(await chrome.storage.local.get(FTE_STATE_STORAGE_KEY))?.[FTE_STATE_STORAGE_KEY]||i;const o=t?.fteConfig?.tooltip;return this?.shouldResetFteToolTip(o,e)&&(i.count=0,i.nextDate=e),chrome.storage.local.set({[FTE_STATE_STORAGE_KEY]:i}),i}constructor(){import(chrome.runtime.getURL("content_scripts/gsuite/fte-utils.js")).then((t=>this.fteUtils=t)),this.eligibilityCheckCount=0,this.tabId="",this.touchPointConfig={},this.addStorageListener()}addStorageListener(){chrome.storage.onChanged.addListener(((t,e)=>{if("local"===e&&this.tabId)for(let e in t)if(e===`${this?.tabId}-embedded-pdf-touch-point`){const{newValue:i}=t[e];this.touchPointConfig=i;break}}))}id="embeddedpdfscoachmark";timeout=1e4;async render(){const t=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});t?.enableEmbeddedPDFTouchPoint&&chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-fte",frameId:this.touchPointConfig?.frameId})}isTouchPointPresent(){return this.touchPointConfig?.visible}async isEligible(){const t=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});if(!t?.enableEmbeddedPDFTouchPoint)return Promise.resolve(!1);let e,i=new Promise((t=>{e=t}));const o=await this.initFteStateAndConfig(t);this.tabId=t?.tabId;const n=setInterval((async()=>{if(this.eligibilityCheckCount<3){if(this.eligibilityCheckCount++,this.fteUtils&&this.isTouchPointPresent()){const i=t?.fteConfig?.tooltip;this.fteUtils?.shouldShowFteTooltip(i,o,!!i).then((t=>{e(t),clearInterval(n)}))}}else e(!1),clearInterval(n)}),3e3);return i}}