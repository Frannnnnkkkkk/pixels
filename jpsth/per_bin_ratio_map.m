close all;
gen_ratio_map=true;
if gen_ratio_map
    load('join_reg_set.mat');
%     load(sprintf('pair_mat_duo_6s_%d_%d.mat',bin,bin+1),'pair_mat');
%     load('conn_mat_duo_6s_1_2.mat','conn_mat');
   
    reg_set=join_reg_set;
    reg_set=reg_set(~strcmp(reg_set,'Unlabeled'));
    reg_set=reg_set(~strcmp(reg_set,'root'));
    keep=true(length(reg_set),1);
    pair_list=cell(6,1);
    conn_list=cell(6,1);
    ratio_list=cell(6,1);
    for bin=1:6
%         load(sprintf('conn_mat_duo_6s_%d_%d.mat',bin,bin+1));
        load(sprintf('pair_mat_duo_6s_%d_%d.mat',bin,bin+1));
%         pair_mat(pair_mat<10)=0;
        pair_list{bin}=pair_mat;
        for i=1:length(pair_mat)
            if nnz(pair_mat(i,:)<20)+nnz(pair_mat(:,i)<20)>=192
                keep(i)=false;
            end
%             disp(nnz(keep));
        end
    end
    reg_keep=reg_set(keep);
    % nnz(keep) likely around 27
%     keyboard
    mean_ratio=zeros(nnz(keep),1);
    for bin =1:6
        load(sprintf('conn_mat_duo_6s_%d_%d.mat',bin,bin+1));
        conn_list{bin}=conn_mat;
        conn_mat_k=conn_mat(keep,keep);
        pair_mat_k=pair_list{bin}(keep,keep);
        ratio_mat=conn_mat_k./pair_mat_k;
        ratio_list{bin}=ratio_mat;
        for i=1:length(ratio_mat)
            mean_ratio(i)=mean_ratio(i)+nanmean(ratio_mat(i,:))+nanmean(ratio_mat(:,i));
        end
    end
%     keyboard
[~,ratioIdx]=sort(mean_ratio);
    for bin=1:6
%         load(sprintf('conn_mat_duo_6s_%d_%d.mat',bin,bin+1));
%         load(sprintf('pair_mat_duo_6s_%d_%d.mat',bin,bin+1));
% 
%         pair_mat_k=pair_mat(keep,keep);
%         conn_mat_k=conn_mat(keep,keep);
%         reg_keep=reg_set(keep);
%         
%         ratio_mat=conn_mat_k./pair_mat_k;
%         sum_ratio=zeros(length(ratio_mat),1);
%         for i=1:length(ratio_mat)
%             sum_ratio(i)=nansum(ratio_mat(i,:))+nansum(ratio_mat(:,i));
%         end
        %
%         sort_mat=ratio_mat;
%         sort_mat(isnan(sort_mat))=nanmean(ratio_mat(:));
        
        %     T=clusterdata(sort_mat,'criterion','distance','linkage','complete','maxclust',3);
        %     T = kmeans(sort_mat,3,'Distance','sqeuclidean','Display','off','MaxIter',100000); 
        %     I=T*1000+(1:length(sort_mat))';
%         [~,indices]=sort(sum_ratio);
        %     [~,indices]=sort(I);
        figure('Color','w','Position',[100,100,450,400])
        h=imagesc(ratio_list{bin}(ratioIdx,ratioIdx),[0,0.2]);
        
        set(h,'alphadata',~isnan(ratio_list{bin}(ratioIdx,ratioIdx))); 
        ax=gca();
        ax.YTick=(1:nnz(keep));
        ax.YTickLabel=reg_keep(ratioIdx);
        
        
        ax.XTick=(1:nnz(keep));
        ax.XTickLabel=reg_keep(ratioIdx);
        ax.XTickLabelRotation=90;
        
        ax.YDir='normal';
        ax.Color=[0.5,0.5,0.5];
        ylabel('target');
        xlabel('source');
        %     colormap('jet')
        colorbar;
        
%         print(sprintf('ratio_map_%d_%d.pdf',bin,bin+1),'-dpdf','-painters','-r300')
%         print(sprintf('ratio_map_%d_%d.png',bin,bin+1),'-dpng','-painters','-r300')
    end
    return
end
