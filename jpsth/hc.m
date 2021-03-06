close all
load('join_reg_set.mat')
load('reg_keep.mat')

allkeep=~ismember(join_reg_set,{'Unlabeled','root'});
all_reg=join_reg_set(allkeep);
major=cellfun(@(x) ~isempty(regexp(x,'[A-Z]','match','once')), all_reg);

conn_list=cell(6,1);
pair_list=cell(6,1);
c_mat_sum=zeros(length(all_reg));
p_mat_sum=zeros(length(all_reg));
zero_count=zeros(size(all_reg));
for bin=1:6
    load(sprintf('conn_mat_duo_6s_%d_%d.mat',bin,bin+1))
    load(sprintf('pair_mat_duo_6s_%d_%d.mat',bin,bin+1))
    conn_list{bin}=conn_mat;
    pair_list{bin}=pair_mat;
    for i=1:length(all_reg)
        zero_count(i)=zero_count(i)+nnz(pair_mat(i,:)==0)+nnz(pair_mat(:,i)==0);
    end
    c_mat_sum=c_mat_sum+conn_mat;
    p_mat_sum=p_mat_sum+pair_mat;
    
end

keep=zero_count<1152;
pkeep=false(size(all_reg));
pkeep(keep)=true;
ckeep=(pkeep & major);
reg_keep=all_reg(ckeep);
save('reg_keep.mat','all_reg','ckeep','reg_keep','-append');

disp(nnz(ckeep));
p_mat_sum(p_mat_sum<10)=0;
rrmat=c_mat_sum(ckeep,ckeep)./p_mat_sum(ckeep,ckeep);
minv=nanmin(rrmat(rrmat>0));
ratio_mat=log10(c_mat_sum(ckeep,ckeep)./p_mat_sum(ckeep,ckeep)+minv/2);
keep_reg=all_reg(ckeep);
D=pdist(ratio_mat',@nan_spearman);
Z=linkage(D,'average');
leafOrder = optimalleaforder(Z,D,'Criteria','group');
figure('Color','w')
[H,T,outperm]=dendrogram(Z,4,'Orientation','left','ColorThreshold','default','Reorder',leafOrder,'Labels',keep_reg);
plot_sel=true;
if plot_sel
    for bin=1:6
        conn_mat=conn_list{bin};
        pair_mat=pair_list{bin};
        keyboard
        ratio_mat=log10(conn_mat(ckeep,ckeep)./pair_mat(ckeep,ckeep)+minv/2);
        fh=figure('Color','w','Position',[100,100,420,380]);
        h=imagesc(ratio_mat(leafOrder,leafOrder),[-3,0]);
        set(h,'alphadata',~isnan(ratio_mat)); 
        colormap(zcmap./255);
        colorbar
        set(gca,'FontSize',6.5,'xaxisLocation','top','XTick',1:nnz(ckeep),'YTick',1:nnz(ckeep),'XTickLabel',keep_reg(leafOrder),'YTickLabel',keep_reg(leafOrder),'XTickLabelRotation',90,'Color',[58 56 56]./255);

    %     set(fh,'PaperSize',[15,10])
        exportgraphics(fh,sprintf('ratio_mat_6s_%d_%d.pdf',bin,bin+1),'Resolution',300)
    %     set(fh, 'PaperPosition', [0 0 12 12])
        print(fh,sprintf('ratio_mat_6s_%d_%d.png',bin,bin+1),'-dpng','-r300')

    end
end

plot_non_sel=true
if plot_non_sel
    for bin=1
        nsconnfstr=load('nonsel_conn_mat_duo_6s_1_2.mat');
        nspairfstr=load('nonsel_pair_mat_duo_6s_1_2.mat');
        conn_mat=nsconnfstr.conn_mat;
        pair_mat=nspairfstr.pair_mat;
        ratio_mat=log10(conn_mat(ckeep,ckeep)./pair_mat(ckeep,ckeep)+minv/2);
        fh=figure('Color','w','Position',[100,100,420,380]);
        h=imagesc(ratio_mat(leafOrder,leafOrder),[-3,0]);
        set(h,'alphadata',~isnan(ratio_mat)); 
        colormap(zcmap./255);
        colorbar
        set(gca,'FontSize',6.5,'xaxisLocation','top','XTick',1:nnz(ckeep),'YTick',1:nnz(ckeep),'XTickLabel',keep_reg(leafOrder),'YTickLabel',keep_reg(leafOrder),'XTickLabelRotation',90,'Color',[58 56 56]./255);

    %     set(fh,'PaperSize',[15,10])
        exportgraphics(fh,sprintf('nonsel_ratio_mat_6s_%d_%d.pdf',bin,bin+1),'Resolution',300)
    %     set(fh, 'PaperPosition', [0 0 12 12])
        print(fh,sprintf('ratio_mat_6s_%d_%d.png',bin,bin+1),'-dpng','-r300')
    end
end



return

for bin=1
    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%Generate data export for gephi network figure%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    conn_mat=conn_list{bin};
    pair_mat=pair_list{bin};
    ratio_mat=conn_mat(ckeep,ckeep)./pair_mat(ckeep,ckeep);
    
    csvcell=cell(1,4);
    csvcell(1,:)={'Id','Label','Interval','Partition'};
    for i=1:length(ratio_mat)
        csvcell(end+1,:)={keep_reg{i},keep_reg{i},[],T(i)};
    end
    
    writecell(csvcell,sprintf('node_exp_%d.csv',bin));
    
    csvcell=cell(1,3);
    csvcell(1,:)={'Source','Target','Weight'};
    for i=1:length(ratio_mat)
        for j=1:length(ratio_mat)
            if ~isnan(ratio_mat(i,j)) && ~(i==j)
                csvcell(end+1,:)={keep_reg{j},keep_reg{i},ratio_mat(i,j)};
            end
        end
    end
    
    writecell(csvcell,sprintf('ratio_mat_conn_%d.csv',bin));
    %%%%%%%%%%%%%% End of GEPHI EXPORT %%%%%%%%%%%%%%%%%%%%%%%
%     keyboard
    
%     G = digraph(ratio_mat,keep_reg,'omitselfloops');
%     fh=figure('Color','w');
%     plot(G, 'LineWidth', G.Edges.Weight*5,'EdgeAlpha',0.5,'ArrowSize',6,'Layout','force')
%     keyboard
%     set(fh,'visible','off')
%     set(fh,'PaperSize',[15,10])
%     print(fh,sprintf('connection_force_%d_%d.pdf',bin_range(1),bin_range(2)),'-dpdf','-r300')
%     set(fh, 'PaperPosition', [0 0 12 12])
%     print(fh,sprintf('connection_force_%d_%d.png',bin_range(1),bin_range(2)),'-dpng','-r300')

end


function  out=nan_spearman(XI,XJ)
if min(size(XJ))==1
    sel= ~(isnan(XI) | isnan(XJ)| isinf(XI) | isinf(XJ));
    if nnz(sel)<3
        out=2;
    else
        NI=XI(sel);
        NJ=XJ(sel);
        nand=corr(NI(:),NJ(:),'type','Spearman');
        out=1-nand;
        if isnan(out)
            out=2;
        end
    end

else
    nand=zeros(size(XJ,1),1);
    for i=1:size(XJ,1)
%         disp(i)
        sel= ~(isnan(XI) | isnan(XJ(i,:))| isinf(XI) | isinf(XJ(i,:)));
        if nnz(sel)<3
            nand(i)=-1;
        else
            NI=XI(sel);
            NJ=XJ(i,sel);
            roh=corr(NI(:),NJ(:),'type','Spearman');
            nand(i)=roh;
            if isnan(roh)
                nand(i)=-1;
            end
        end
    end
    out=1-nand;
end
end


